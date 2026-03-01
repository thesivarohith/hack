from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Header
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Source, Schedule, Mastery, init_db
from backend.rag_engine import ingest_document, query_knowledge_base
from backend.student_data import StudentProfileManager
import shutil
import os
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid

# Create tables
init_db()

app = FastAPI(title="FocusFlow Backend")

# Health check endpoint for container startup
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/config")
async def get_config():
    from backend.config import IS_CLOUD, DEPLOYMENT_MODE
    return {
        "is_cloud": IS_CLOUD,
        "deployment_mode": DEPLOYMENT_MODE,
        "youtube_enabled": not IS_CLOUD
    }

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Get student profile manager per session
def get_profile_manager(authorization: Optional[str] = Header(None)) -> StudentProfileManager:
    """Get profile manager with session-specific student ID from Firebase token."""
    from backend.config import is_firebase_configured

    if is_firebase_configured():
        # Cloud mode: require a valid Firebase token
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
        token = authorization.replace("Bearer ", "", 1)
        from backend.firebase_auth import verify_firebase_token
        decoded = verify_firebase_token(token)
        student_id = decoded["uid"]
    else:
        # Local mode fallback: no Firebase → use fixed local user
        student_id = "local_user"

    return StudentProfileManager(student_id=student_id)

# Pydantic Models
class ScheduleItem(BaseModel):
    id: int
    date: str
    topic_name: str
    is_completed: bool
    is_locked: bool

class SourceItem(BaseModel):
    id: int
    filename: str
    type: str
    is_active: bool

class UnlockRequest(BaseModel):
    topic_id: int
    quiz_score: int

class UnlockResponse(BaseModel):
    success: bool
    message: str
    next_topic_unlocked: bool

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = f"data/{file.filename}"
    try:
        with open(file_location, "wb+") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    # Ingest
    try:
        ingest_document(file_location)
    except Exception as e:
        # cleanup if ingest fails?
        # os.remove(file_location)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    
    # Save to DB
    new_source = Source(filename=file.filename, type="local", file_path=file_location, is_active=True)
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    
    return {"message": "File uploaded and ingested successfully", "id": new_source.id}
    return {"message": "File uploaded and ingested successfully", "id": new_source.id}

class UrlRequest(BaseModel):
    url: str

@app.post("/ingest_url")
def ingest_url_endpoint(request: UrlRequest, db: Session = Depends(get_db)):
    try:
        from backend.rag_engine import ingest_url
        title = ingest_url(request.url)
        
        # Save to DB
        # We use the title as the filename for display purposes
        new_source = Source(filename=title, type="url", file_path=request.url, is_active=True)
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        return {"message": f"Successfully added: {title}", "id": new_source.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TextIngestionRequest(BaseModel):
    text: str
    source_name: str
    source_type: str = "text"

@app.post("/ingest_text")
def ingest_text_endpoint(request: TextIngestionRequest, db: Session = Depends(get_db)):
    """Ingest raw text content (e.g. browser-fetched YouTube transcripts)."""
    try:
        from backend.rag_engine import ingest_text
        title = ingest_text(request.text, request.source_name, request.source_type)

        # Save to DB
        new_source = Source(filename=title, type=request.source_type, file_path=request.source_name, is_active=True)
        db.add(new_source)
        db.commit()
        db.refresh(new_source)

        return {"message": f"Successfully added: {title}", "id": new_source.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class YouTubeIngestionRequest(BaseModel):
    video_id: str

@app.post("/ingest_youtube")
def ingest_youtube(request: YouTubeIngestionRequest, db: Session = Depends(get_db)):
    try:
        from backend.rag_engine import get_youtube_transcript, ingest_text
        # Fetch transcript using Invidious
        transcript_text = get_youtube_transcript(request.video_id)

        # Run through existing ingestion pipeline
        source_name = f"YouTube: {request.video_id}"
        title = ingest_text(
            text=transcript_text,
            source_name=source_name,
            source_type="youtube"
        )

        # Save to DB
        new_source = Source(filename=title, type="youtube", file_path=source_name, is_active=True)
        db.add(new_source)
        db.commit()
        db.refresh(new_source)

        return {"status": "success", "message": f"Successfully added: {title}", "source": source_name, "id": new_source.id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process YouTube video: {str(e)}"
        )


@app.get("/sources", response_model=List[SourceItem])
def get_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).filter(Source.is_active == True).all()
    return sources

@app.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Soft delete
    try:
        from backend.rag_engine import delete_document
        delete_document(source.file_path)
    except Exception as e:
        print(f"Failed to delete from vector store: {e}")

    source.is_active = False
    db.commit()
    return {"success": True, "message": "Source deleted"}

@app.get("/schedule/{date}", response_model=List[ScheduleItem])
def get_schedule(date: str, db: Session = Depends(get_db)):
    # Assuming date is YYYY-MM-DD
    schedule_items = db.query(Schedule).filter(Schedule.date == date).all()
    if not schedule_items:
        # Just return empty list or maybe 404? 
        return []
    return schedule_items

@app.post("/unlock_topic", response_model=UnlockResponse)
def unlock_topic(request: UnlockRequest, db: Session = Depends(get_db)):
    # 1. Update Mastery or Schedule completion
    # Find the schedule item for this topic_id (Assuming topic_id refers to Schedule ID for simplicity, or we link Mastery to Schedule)
    # The prompt says: Takes a topic_id and quiz_score.
    
    # Let's find the current topic in Schedule
    current_topic = db.query(Schedule).filter(Schedule.id == request.topic_id).first()
    if not current_topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    # Update Mastery logic (not explicitly detailed in prompt how Mastery links, but we can creating/update a Mastery record)
    # Check if mastery exists for this topic name
    mastery = db.query(Mastery).filter(Mastery.topic_name == current_topic.topic_name).first()
    if not mastery:
        mastery = Mastery(topic_name=current_topic.topic_name, quiz_score=request.quiz_score)
        db.add(mastery)
    else:
        mastery.quiz_score = request.quiz_score
    
    # Update current topic completion if passed? Prompt doesn't specify, but implies progress.
    if request.quiz_score > 60:
        current_topic.is_completed = True
        
        # Unlock next topic
        # Logic: Find next topic by ID (assuming sequential)
        next_topic = db.query(Schedule).filter(Schedule.id > current_topic.id).order_by(Schedule.id.asc()).first()
        
        next_unlocked = False
        if next_topic:
            next_topic.is_locked = False
            next_unlocked = True
            
        db.commit()
        return {"success": True, "message": "Quiz Passed! Next topic unlocked.", "next_topic_unlocked": next_unlocked}
    else:
        db.commit()
        return {"success": False, "message": "Score too low. Try again!", "next_topic_unlocked": False}

class PlanRequest(BaseModel):
    request_text: str

@app.post("/generate_plan")
def generate_plan_endpoint(request: PlanRequest):
    try:
        from backend.rag_engine import generate_study_plan
        plan = generate_study_plan(request.request_text)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class QueryRequest(BaseModel):
    question: str
    history: List[dict] = []

@app.post("/query")
async def query_kb(request: QueryRequest):
    """
    RAG query endpoint.
    """
    from backend.rag_engine import query_knowledge_base
    response = query_knowledge_base(request.question, request.history)
    return response

class LessonRequest(BaseModel):
    topic: str

@app.post("/generate_lesson")
def generate_lesson_endpoint(request: LessonRequest, db: Session = Depends(get_db)):
    try:
        from backend.rag_engine import generate_lesson_content
        content = generate_lesson_content(request.topic)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class QuizRequest(BaseModel):
    topic: str

@app.post("/generate_quiz")
def generate_quiz_endpoint(request: QuizRequest):
    try:
        from backend.rag_engine import generate_quiz_data
        quiz_data = generate_quiz_data(request.topic)
        return {"quiz": quiz_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== STUDENT PROFILE ENDPOINTS ==========

@app.get("/student/profile")
def get_student_profile(profile_manager: StudentProfileManager = Depends(get_profile_manager)):
    """Load student profile"""
    try:
        profile = profile_manager.load_profile()
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SaveProgressRequest(BaseModel):
    current_day: int
    current_topic_id: Optional[int]
    plan_id: Optional[str]

@app.post("/student/save_progress")
def save_progress(request: dict, profile_manager: StudentProfileManager = Depends(get_profile_manager)):
    """Save current study state"""
    try:
        profile = profile_manager.load_profile()
        
        # Update current study day if provided
        if "current_study_day" in request:
            profile["current_study_day"] = request["current_study_day"]
        
        # Update last access date if provided
        if "last_access_date" in request:
            profile["last_access_date"] = request["last_access_date"]
        
        # Legacy support for current_day and current_topic_id
        if "current_day" in request:
            profile["current_study_day"] = request["current_day"]
        if "current_topic_id" in request:
            profile.setdefault("current_topic_id", request["current_topic_id"])
        if "plan_id" in request:
            if "study_plan" in profile:
                profile["study_plan"]["plan_id"] = request["plan_id"]
        
        profile_manager.save_profile(profile)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SavePlanRequest(BaseModel):
    topics: List[Dict]
    num_days: int

@app.post("/student/save_plan")
def save_study_plan(request: SavePlanRequest, profile_manager: StudentProfileManager = Depends(get_profile_manager)):
    """Save generated study plan"""
    try:
        plan_id = profile_manager.save_study_plan(request.topics, request.num_days)
        return {"status": "saved", "plan_id": plan_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class QuizCompleteRequest(BaseModel):
    topic_id: int
    topic_title: str
    subject: str
    score: int
    total: int
    time_taken: int = 0

@app.post("/student/quiz_complete")
def record_quiz(request: QuizCompleteRequest, profile_manager: StudentProfileManager = Depends(get_profile_manager)):
    """Record quiz completion"""
    try:
        profile_manager.update_quiz_score(
            request.topic_id,
            request.topic_title,
            request.subject,
            request.score,
            request.total,
            request.time_taken
        )
        profile_manager.mark_topic_complete(request.topic_id)
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/student/mastery")
def get_mastery_data(profile_manager: StudentProfileManager = Depends(get_profile_manager)):
    """Get subject mastery data"""
    try:
        mastery = profile_manager.get_mastery_data()
        return {"mastery": mastery}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class IncompleteTaskRequest(BaseModel):
    topic_id: int
    from_day: int
    reason: str = "not_completed"

@app.post("/student/incomplete_task")
def add_incomplete_task(request: IncompleteTaskRequest, profile_manager: StudentProfileManager = Depends(get_profile_manager)):
    """Mark a task as incomplete"""
    try:
        profile_manager.add_incomplete_task(
            request.topic_id,
            request.from_day,
            request.reason
        )
        return {"status": "added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/student/incomplete_tasks/{current_day}")
def get_incomplete_tasks(current_day: int, profile_manager: StudentProfileManager = Depends(get_profile_manager)):
    """Get incomplete tasks from previous days"""
    try:
        tasks = profile_manager.get_incomplete_tasks(current_day)
        return {"incomplete_tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))