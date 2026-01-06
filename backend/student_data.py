"""
Student Profile Manager - Handles persistent storage of student learning data
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading

class StudentProfileManager:
    """Manages student profile data with JSON file persistence"""
    
    def __init__(self):
        self.profile_dir = Path.home() / ".focusflow"
        self.profile_file = self.profile_dir / "student_profile.json"
        self.backup_file = self.profile_dir / "student_profile.backup.json"
        self.lock = threading.Lock()
        self._ensure_profile_exists()
    
    def _ensure_profile_exists(self):
        """Create profile directory and file if not exists"""
        self.profile_dir.mkdir(exist_ok=True)
        
        if not self.profile_file.exists():
            # Create new profile with default structure
            default_profile = {
                "student_id": f"student_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "current_state": {
                    "current_day": 1,
                    "current_topic_id": None,
                    "active_plan_id": None
                },
                "study_plan": {
                    "plan_id": None,
                    "created_at": None,
                    "num_days": 0,
                    "topics": []
                },
                "quiz_history": [],
                "mastery_tracker": {},
                "time_tracking": {
                    "total_study_time_minutes": 0,
                    "topics_time": {}
                },
                "incomplete_tasks": []
            }
            self._save_to_file(default_profile)
    
    def _save_to_file(self, profile: dict):
        """Atomic write to file with backup"""
        try:
            # Create backup of existing file
            if self.profile_file.exists():
                shutil.copy2(self.profile_file, self.backup_file)
            
            # Write to temporary file first
            temp_file = self.profile_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(profile, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.profile_file)
            
        except Exception as e:
            print(f"Error saving profile: {e}")
            # Restore from backup if exists
            if self.backup_file.exists():
                shutil.copy2(self.backup_file, self.profile_file)
            raise
    
    def load_profile(self) -> dict:
        """Load student profile from disk"""
        with self.lock:
            try:
                with open(self.profile_file, 'r') as f:
                    profile = json.load(f)
                
                # Update last active
                profile["last_active"] = datetime.now().isoformat()
                self._save_to_file(profile)
                
                return profile
            except Exception as e:
                print(f"Error loading profile: {e}")
                # Return default profile
                self._ensure_profile_exists()
                return self.load_profile()
    
    def save_profile(self, profile: dict):
        """Save student profile to disk"""
        with self.lock:
            profile["last_active"] = datetime.now().isoformat()
            self._save_to_file(profile)
    
    def update_current_state(self, current_day: int, current_topic_id: Optional[int], plan_id: Optional[str]):
        """Update current position in study plan"""
        profile = self.load_profile()
        profile["current_state"] = {
            "current_day": current_day,
            "current_topic_id": current_topic_id,
            "active_plan_id": plan_id
        }
        self.save_profile(profile)
    
    def save_study_plan(self, topics: List[dict], num_days: int):
        """Save study plan"""
        profile = self.load_profile()
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        profile["study_plan"] = {
            "plan_id": plan_id,
            "created_at": datetime.now().isoformat(),
            "num_days": num_days,
            "topics": topics
        }
        profile["current_state"]["active_plan_id"] = plan_id
        
        self.save_profile(profile)
        return plan_id
    
    def update_quiz_score(self, topic_id: int, topic_title: str, subject: str, score: int, total: int, time_taken: int = 0):
        """Record quiz performance"""
        profile = self.load_profile()
        
        percentage = (score / total * 100) if total > 0 else 0
        
        # Add to quiz history
        quiz_record = {
            "topic_id": topic_id,
            "topic_title": topic_title,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "total": total,
            "percentage": percentage,
            "time_taken_seconds": time_taken
        }
        profile["quiz_history"].append(quiz_record)
        
        # Update mastery tracker
        self._update_mastery(profile, subject, percentage)
        
        self.save_profile(profile)
    
    def _update_mastery(self, profile: dict, subject: str, score_percentage: float):
        """Update subject mastery level"""
        if subject not in profile["mastery_tracker"]:
            profile["mastery_tracker"][subject] = {
                "avg_score": 0,
                "topics_completed": 0,
                "total_topics": 0,
                "mastery_level": "medium",
                "scores": []
            }
        
        mastery = profile["mastery_tracker"][subject]
        mastery["scores"].append(score_percentage)
        mastery["topics_completed"] += 1
        
        # Calculate average
        mastery["avg_score"] = sum(mastery["scores"]) / len(mastery["scores"])
        
        # Determine mastery level
        avg = mastery["avg_score"]
        if avg >= 75:
            mastery["mastery_level"] = "high"
        elif avg >= 50:
            mastery["mastery_level"] = "medium"
        else:
            mastery["mastery_level"] = "low"
    
    def mark_topic_complete(self, topic_id: int, completed_at: Optional[str] = None):
        """Mark a topic as completed"""
        profile = self.load_profile()
        
        if not completed_at:
            completed_at = datetime.now().isoformat()
        
        # Update topic in study plan
        for topic in profile["study_plan"]["topics"]:
            if topic["id"] == topic_id:
                topic["status"] = "completed"
                topic["completed_at"] = completed_at
                break
        
        # Remove from incomplete tasks if present
        profile["incomplete_tasks"] = [
            t for t in profile["incomplete_tasks"] if t["topic_id"] != topic_id
        ]
        
        self.save_profile(profile)
    
    def add_incomplete_task(self, topic_id: int, from_day: int, reason: str = "not_completed"):
        """Mark a task as incomplete"""
        profile = self.load_profile()
        
        # Check if already in incomplete list
        if not any(t["topic_id"] == topic_id for t in profile["incomplete_tasks"]):
            profile["incomplete_tasks"].append({
                "topic_id": topic_id,
                "from_day": from_day,
                "reason": reason,
                "added_at": datetime.now().isoformat()
            })
        
        self.save_profile(profile)
    
    def get_incomplete_tasks(self, current_day: int) -> List[dict]:
        """Get tasks not completed from previous days"""
        profile = self.load_profile()
        
        # Get incomplete tasks from previous days
        return [
            t for t in profile["incomplete_tasks"] 
            if t["from_day"] < current_day
        ]
    
    def get_mastery_data(self) -> Dict[str, dict]:
        """Get mastery tracker data"""
        profile = self.load_profile()
        return profile.get("mastery_tracker", {})
    
    def record_study_time(self, topic_id: int, minutes: int):
        """Record time spent on a topic"""
        profile = self.load_profile()
        
        profile["time_tracking"]["total_study_time_minutes"] += minutes
        
        topic_id_str = str(topic_id)
        if topic_id_str not in profile["time_tracking"]["topics_time"]:
            profile["time_tracking"]["topics_time"][topic_id_str] = 0
        
        profile["time_tracking"]["topics_time"][topic_id_str] += minutes
        
        self.save_profile(profile)
