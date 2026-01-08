"""
Supabase storage adapter for student profiles.
Provides persistent storage for HF Spaces deployment.
"""
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SupabaseStorage:
    """
    Handles student profile storage in Supabase PostgreSQL.
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client = None
        self.table_name = "student_profiles"
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client with error handling"""
        try:
            from supabase import create_client
            
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            
            if not url or not key:
                logger.warning("Supabase credentials not found in environment")
                return
            
            self.client = create_client(url, key)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Supabase storage is available"""
        return self.client is not None
    
    def save_profile(self, student_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Save student profile to Supabase.
        
        Args:
            student_id: Unique student identifier
            profile_data: Profile data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.warning("Supabase not available for save operation")
            return False
        
        try:
            # Check if profile exists
            existing = self.client.table(self.table_name)\
                .select("id")\
                .eq("student_id", student_id)\
                .execute()
            
            profile_json = {
                "student_id": student_id,
                "profile_data": profile_data,
                "updated_at": datetime.now().isoformat()
            }
            
            if existing.data:
                # Update existing profile
                result = self.client.table(self.table_name)\
                    .update(profile_json)\
                    .eq("student_id", student_id)\
                    .execute()
            else:
                # Insert new profile
                profile_json["created_at"] = datetime.now().isoformat()
                result = self.client.table(self.table_name)\
                    .insert(profile_json)\
                    .execute()
            
            logger.info(f"Profile saved successfully for student: {student_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save profile to Supabase: {e}")
            return False
    
    def load_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Load student profile from Supabase.
        
        Args:
            student_id: Unique student identifier
            
        Returns:
            Profile data dictionary or None if not found
        """
        if not self.is_available():
            logger.warning("Supabase not available for load operation")
            return None
        
        try:
            result = self.client.table(self.table_name)\
                .select("profile_data")\
                .eq("student_id", student_id)\
                .execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Profile loaded successfully for student: {student_id}")
                return result.data[0]["profile_data"]
            else:
                logger.info(f"No profile found for student: {student_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load profile from Supabase: {e}")
            return None
    
    def profile_exists(self, student_id: str) -> bool:
        """
        Check if profile exists in Supabase.
        
        Args:
            student_id: Unique student identifier
            
        Returns:
            True if profile exists, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            result = self.client.table(self.table_name)\
                .select("id")\
                .eq("student_id", student_id)\
                .execute()
            
            return result.data and len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to check profile existence: {e}")
            return False
