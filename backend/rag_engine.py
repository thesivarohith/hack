import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.llms import Ollama
from backend.config import get_llm, get_embeddings, has_youtube_api_key, YOUTUBE_API_KEY
from langchain_core.documents import Document
import logging
import time
import re

# Configure logger FIRST
logger = logging.getLogger(__name__)

# YouTube transcript support
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound, InvalidVideoId
    HAS_YOUTUBE_API = True
except ImportError:
    HAS_YOUTUBE_API = False
    logger.warning("youtube-transcript-api not installed - YouTube local fallback will not work")

CACHE_DIR = "./chroma_db"


def _parse_srt_to_text(srt_content: str) -> str:
    """Parse SRT subtitle format to plain text."""
    lines = srt_content.split('\n')
    text_lines = []
    for line in lines:
        line = line.strip()
        # Skip empty lines, sequence numbers, and timestamp lines
        if not line:
            continue
        if line.isdigit():
            continue
        if re.match(r'\d{2}:\d{2}:\d{2}', line):
            continue
        text_lines.append(line)
    return ' '.join(text_lines)


def _fetch_youtube_transcript(video_id: str) -> tuple:
    """
    Fetch YouTube transcript using the best available method.
    Returns (transcript_text, caption_type) tuple.
    
    Method A: YouTube Data API v3 (when YOUTUBE_API_KEY is set - reliable in cloud)
    Method B: youtube-transcript-api fallback (local mode)
    """
    
    # --- METHOD A: YouTube Data API v3 (cloud-reliable) ---
    if has_youtube_api_key():
        logger.info("Using YouTube Data API v3 (API key found)")
        try:
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            
            youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
            
            # Get available caption tracks
            captions_response = youtube.captions().list(
                part='snippet',
                videoId=video_id
            ).execute()
            
            caption_items = captions_response.get('items', [])
            
            if not caption_items:
                raise ValueError(
                    "No captions found for this video. "
                    "The video may have captions disabled by the creator."
                )
            
            # Select best caption track by priority
            selected_track = None
            caption_type = "manual"
            
            # Priority 1: Manual English
            for item in caption_items:
                snippet = item['snippet']
                if snippet.get('language') == 'en' and snippet.get('trackKind') == 'standard':
                    selected_track = item
                    caption_type = "manual"
                    break
            
            # Priority 2: Auto-generated English
            if not selected_track:
                for item in caption_items:
                    snippet = item['snippet']
                    if snippet.get('language') == 'en' and snippet.get('trackKind') == 'asr':
                        selected_track = item
                        caption_type = "auto-generated"
                        break
            
            # Priority 3: Any manual caption
            if not selected_track:
                for item in caption_items:
                    snippet = item['snippet']
                    if snippet.get('trackKind') == 'standard':
                        selected_track = item
                        caption_type = "manual"
                        break
            
            # Priority 4: Any auto-generated caption
            if not selected_track:
                for item in caption_items:
                    selected_track = item
                    caption_type = "auto-generated"
                    break
            
            if not selected_track:
                raise ValueError(
                    "No captions found for this video. "
                    "The video may have captions disabled by the creator."
                )
            
            logger.info(f"Selected caption track: {selected_track['snippet'].get('language')} ({caption_type})")
            
            # Download the caption track
            caption_id = selected_track['id']
            subtitle_response = youtube.captions().download(
                id=caption_id,
                tfmt='srt'
            ).execute()
            
            # Parse SRT to plain text
            srt_text = subtitle_response.decode('utf-8') if isinstance(subtitle_response, bytes) else str(subtitle_response)
            transcript_text = _parse_srt_to_text(srt_text)
            
            if not transcript_text or len(transcript_text) < 50:
                raise ValueError(
                    "Transcript is too short or empty. "
                    "Try a different video with more spoken content."
                )
            
            logger.info(f"YouTube Data API: extracted {len(transcript_text)} chars ({caption_type})")
            return transcript_text, caption_type
            
        except HttpError as e:
            if e.resp.status == 403:
                if 'quotaExceeded' in str(e):
                    raise ValueError(
                        "YouTube API quota exceeded. "
                        "Please try again later or upload a PDF instead."
                    )
                # captions().download requires OAuth for third-party videos
                # Fall through to Method B
                logger.warning(f"YouTube Data API forbidden (likely needs OAuth for captions download): {e}")
                logger.info("Falling back to youtube-transcript-api...")
            elif e.resp.status == 404:
                raise ValueError(
                    "Could not access this video. "
                    "It may be private, deleted, or region-restricted."
                )
            else:
                logger.error(f"YouTube Data API error: {e}")
                logger.info("Falling back to youtube-transcript-api...")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"YouTube Data API unexpected error: {e}")
            logger.info("Falling back to youtube-transcript-api...")
    
    # --- METHOD B: youtube-transcript-api fallback (local / API fallback) ---
    if not HAS_YOUTUBE_API:
        raise ValueError(
            "YouTube transcript libraries not available. "
            "Please upload a PDF instead."
        )
    
    logger.info("Using youtube-transcript-api (local fallback)")
    ytt = YouTubeTranscriptApi()
    
    try:
        # PRIORITY 1: Try manual English captions
        logger.info("Trying manual English captions...")
        transcript = ytt.fetch(video_id, languages=['en'])
        transcript_text = ' '.join([t.text for t in transcript])
        logger.info(f"Got manual English transcript ({len(transcript_text)} chars)")
        return transcript_text, "manual"
    except Exception as e1:
        logger.info(f"Manual English not available: {e1}")
        try:
            # PRIORITY 2: Try any available transcript (includes auto-generated)
            logger.info("Trying any available transcript...")
            transcript_list = ytt.list(video_id)
            first_available = next(iter(transcript_list))
            transcript = first_available.fetch()
            transcript_text = ' '.join([t.text for t in transcript])
            logger.info(f"Got fallback transcript ({len(transcript_text)} chars)")
            return transcript_text, "auto-generated"
        except (TranscriptsDisabled, NoTranscriptFound):
            raise ValueError(
                "No captions found for this video. "
                "This video may have captions disabled entirely. "
                "Try a different video or upload a PDF instead."
            )
        except InvalidVideoId:
            raise ValueError(f"Invalid YouTube video ID: {video_id}. Please check the URL.")
        except StopIteration:
            raise ValueError(
                "No captions found for this video. "
                "This video may have captions disabled entirely. "
                "Try a different video or upload a PDF instead."
            )
        except Exception as e2:
            logger.error(f"All transcript fetch attempts failed: {e2}")
            raise ValueError(
                "No captions found for this video. "
                "This video may have captions disabled entirely. "
                "Try a different video or upload a PDF instead."
            )



def ingest_document(file_path: str):
    """
    Ingests a PDF document into the vector database.
    Falls back to OCR (pytesseract) if standard text extraction yields little/no text.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # --- Step 1: Try standard text extraction ---
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # Filter out pages with no real text content
    docs = [d for d in docs if d.page_content.strip()]

    # Check total extracted text length
    total_text = "".join(d.page_content.strip() for d in docs)

    # --- Step 2: OCR fallback if text is too short ---
    if len(total_text) < 50:
        logger.info(f"Standard extraction found only {len(total_text)} chars, attempting OCR fallback...")
        try:
            from pdf2image import convert_from_path
            import pytesseract

            # Convert PDF pages to images at 300 DPI
            images = convert_from_path(file_path, dpi=300)
            ocr_pages = []

            for page_num, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                if page_text.strip():
                    ocr_pages.append(Document(
                        page_content=page_text,
                        metadata={"source": file_path, "page": page_num}
                    ))

            if ocr_pages:
                ocr_total = "".join(d.page_content.strip() for d in ocr_pages)
                if len(ocr_total) < 50:
                    raise ValueError(
                        "Could not extract text even after OCR. "
                        "Please upload a clearer scan."
                    )
                docs = ocr_pages
                logger.info(f"OCR extracted {len(ocr_total)} chars from {len(ocr_pages)} pages")
            else:
                raise ValueError(
                    "Could not extract text even after OCR. "
                    "Please upload a clearer scan."
                )
        except ImportError:
            logger.warning("pytesseract/pdf2image not installed, cannot OCR")
            raise ValueError(
                "No readable text found and OCR libraries are not available. "
                "Please upload a text-based PDF."
            )
        except ValueError:
            raise  # Re-raise our own clear errors
        except Exception as e:
            logger.error(f"OCR fallback failed: {e}")
            raise ValueError(
                f"OCR processing failed: {str(e)}. "
                "Please try a clearer scan or a text-based PDF."
            )

    # --- Step 3: Split text (unchanged) ---
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)

    if not splits:
        raise ValueError(
            "No readable text found in this PDF. "
            "It may be a scanned/image-only document."
        )
    
    # --- Step 4: Store in ChromaDB (unchanged) ---
    Chroma.from_documents(
        documents=splits,
        embedding=get_embeddings(),
        persist_directory=CACHE_DIR
    )
    # Ingestion successful

def ingest_url(url: str):
    """
    Ingests content from a URL (YouTube or Web).
    Uses YouTube Data API v3 in cloud mode, youtube-transcript-api locally.
    """
    from langchain_community.document_loaders import WebBaseLoader
    
    if not HAS_YOUTUBE_API and not has_youtube_api_key() and ("youtube.com" in url or "youtu.be" in url):
        raise ValueError("YouTube support not available - no API key or transcript library found")
    
    docs = []
    title = url
    
    try:
        # Check if it's a YouTube URL (including shorts)
        is_youtube = "youtube.com" in url or "youtu.be" in url
        
        if is_youtube:
            logger.info(f"Processing YouTube URL: {url}")
            
            # Extract video ID using regex (supports watch, youtu.be, shorts, embed)
            video_id_match = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([a-zA-Z0-9_-]{11})', url)
            video_id = video_id_match.group(1) if video_id_match else None
            
            if not video_id:
                raise ValueError(
                    "Could not extract video ID from YouTube URL. "
                    "Supported formats: youtube.com/watch?v=ID, youtu.be/ID, or youtube.com/shorts/ID"
                )
            
            logger.info(f"Extracted video ID: {video_id}")
            
            # Fetch transcript using the appropriate method
            transcript_text, caption_type = _fetch_youtube_transcript(video_id)
            
            # Clean up transcript text
            transcript_text = re.sub(r'\[.*?\]', '', transcript_text)  # Remove [Music], [Applause], etc.
            transcript_text = re.sub(r'\s+', ' ', transcript_text).strip()  # Normalize whitespace
            
            if len(transcript_text) < 50:
                raise ValueError(
                    "Transcript is too short or empty after cleanup. "
                    "Try a different video with more spoken content."
                )
            
            # Create a document from the transcript
            docs = [Document(
                page_content=transcript_text,
                metadata={
                    "source": url,
                    "title": f"YouTube: {video_id}",
                    "type": "youtube",
                    "caption_type": caption_type
                }
            )]
            title = f"YouTube Video: {video_id} ({caption_type} captions)"
            
        else:
            # Regular web page
            logger.info(f"Processing web page: {url}")
            loader = WebBaseLoader(url)
            loader.requests_kwargs = {'timeout': 30}
            docs = loader.load()
            logger.info(f"Successfully loaded {len(docs)} documents")
            title = docs[0].metadata.get("title", url) if docs else url
            
        # Process and store documents
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = splitter.split_documents(docs)
        
        if not splits:
            raise ValueError("No content found to ingest")
        
        logger.info(f"Split into {len(splits)} chunks, storing in ChromaDB")
            
        # Store in ChromaDB
        Chroma.from_documents(
            documents=splits,
            embedding=get_embeddings(),
            persist_directory=CACHE_DIR
        )
        
        logger.info(f"Successfully ingested: {title}")
        return title
        
    except ValueError as e:
        # User-friendly errors
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error ingesting URL: {e}")
        raise ValueError(f"Failed to process URL: {str(e)}")

def delete_document(source_path: str):
    """
    Removes a document from the vector database by its source path.
    """
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=get_embeddings()
    )
    
    # Delete based on metadata 'source'
    try:
        # Accessing the underlying chroma collection to delete by metadata
        vector_store._collection.delete(where={"source": source_path})

    except Exception as e:
        print(f"Error deleting from ChromaDB: {e}")

# In backend/rag_engine.py


def generate_study_plan(user_request: str):

    
    # Initialize resources
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=get_embeddings()
    )
    llm = get_llm()
    
    # 1. Extract number of days from request (default to 5 if not specified)
    import re
    day_match = re.search(r'(\d+)\s*day', user_request.lower())
    num_days = int(day_match.group(1)) if day_match else 5
    
    # 2. Get documents from MULTIPLE sources
    docs = vector_store.similarity_search("topics subjects syllabus overview", k=20)
    
    # 3. Extract topics grouped by source document (each source = one subject)
    topics_by_source = {}
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        if source not in topics_by_source:
            topics_by_source[source] = {
                "topics": [],
                "subject_name": None  # Will extract subject name from content
            }
        
        content = doc.page_content
        
        # Try to extract subject name from first occurrence
        if topics_by_source[source]["subject_name"] is None:
            # Look for subject indicators in first 200 chars
            first_part = content[:200].upper()
            if "MANUFACTURING" in first_part:
                topics_by_source[source]["subject_name"] = "Manufacturing Technology"
            elif "OOPS" in first_part or "OBJECT" in first_part:
                topics_by_source[source]["subject_name"] = "Object-Oriented Programming"
            elif "DATA STRUCT" in first_part:
                topics_by_source[source]["subject_name"] = "Data Structures"
            else:
                # Use filename as fallback
                filename = source.split('/')[-1].replace('.pdf', '').replace('-', ' ').title()
                topics_by_source[source]["subject_name"] = filename
        
        # Extract topics from content
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 150:
                # Filter for topic-like content
                if any(kw in sentence.lower() for kw in ['topic', 'chapter', 'module', 'unit', 'concept', 'introduction', 'process', 'method']):
                    topics_by_source[source]["topics"].append(sentence)
                elif sentence[0].isupper() and len(sentence.split()) > 4:
                    topics_by_source[source]["topics"].append(sentence)
    
    # Remove duplicates per source and limit
    for source in topics_by_source:
        topics_by_source[source]["topics"] = list(dict.fromkeys(topics_by_source[source]["topics"]))[:num_days * 2]
    
    # 4. Create plan with MULTIPLE TOPICS PER DAY (one from each subject)
    all_sources = list(topics_by_source.keys())
    num_subjects = len(all_sources)

    
    if num_subjects == 0:
        # Fallback if no sources found
        return {
            "days": [
                {"day": i, "topic": f"Topic {i}", "details": "Study material", "status": "unlocked" if i == 1 else "locked", "subject": "General", "id": i}
                for i in range(1, num_days + 1)
            ]
        }
    
    # Generate plan: For each day, create one topic from each subject
    plan_days = []
    topic_id = 1
    
    for day_num in range(1, num_days + 1):
        # For this day, create one topic from each subject
        for source_idx, source in enumerate(all_sources):
            subject_name = topics_by_source[source]["subject_name"]
            source_topics = topics_by_source[source]["topics"]
            
            # Get topic for this day from this subject
            # Use round-robin approach: take different topic for each day
            topic_idx = (day_num - 1) % len(source_topics) if source_topics else 0
            
            if source_topics and topic_idx < len(source_topics):
                topic_text = source_topics[topic_idx]
                # Clean up topic text
                topic_text = topic_text[:100]  # Limit length
            else:
                topic_text = f"Concepts and Principles"
            
            # Create topic entry
            plan_days.append({
                "day": day_num,
                "id": topic_id,
                "subject": subject_name,
                "topic": f"{subject_name}: {topic_text}",
                "details": f"Study material for {subject_name}",
                "status": "unlocked" if day_num == 1 else "locked",
                "quiz_passed": False
            })
            topic_id += 1
    

    return {"days": plan_days}

def generate_lesson_content(topic_title: str):

    
    # Initialize resources
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=get_embeddings()
    )
    llm = get_llm()
    
    # 1. Search DB for comprehensive context (increased from 4 to 8 chunks)
    docs = vector_store.similarity_search(topic_title, k=8)
    context_text = "\n".join([d.page_content[:500] for d in docs])  # Increased from 400 to 500 chars
    
    # 2. Extract source citations
    sources_list = []
    seen_sources = set()
    for doc in docs[:5]:  # Use top 5 sources
        source_file = doc.metadata.get("source", "Unknown")
        source_filename = source_file.split("/")[-1] if "/" in source_file else source_file
        page = doc.metadata.get("page", "N/A")
        
        # Avoid duplicate sources
        source_key = f"{source_filename}_p{page}"
        if source_key not in seen_sources:
            sources_list.append({
                "filename": source_filename,
                "page": page
            })
            seen_sources.add(source_key)
    
    # Build sources reference text
    sources_text = "\n".join([f"- {src['filename']}, page {src['page']}" for src in sources_list])
    
    # 3. Enhanced Educational Prompt for detailed content with citations
    prompt = f"""Create a comprehensive study guide for: {topic_title}

Context from course materials:
{context_text}

Available sources: {sources_text}

Write a DETAILED study guide in Markdown format with these sections:

## Introduction
Explain what this topic is and why it's important (2-3 paragraphs)

## Core Concepts
Break down the main ideas into clear subsections. For each concept:
- Define it clearly
- Explain how it works
- Describe when and why to use it

## Key Points & Rules
List important formulas, rules, syntax, or principles. Include code examples if applicable.

## Practical Examples
Provide 2-3 real-world examples showing:
- The problem scenario
- How the concept solves it
- Step-by-step walkthrough

## Common Mistakes
Highlight typical errors students make and how to avoid them

## Summary
Quick bullet-point recap of key takeaways

IMPORTANT: Add inline citations where appropriate using the format [Source: filename]. 
Make this comprehensive and educational. Aim for 600-800 words. Use clear explanations a student can understand.

Markdown content:"""
    
    # 4. Generate
    try:
        response = llm.invoke(prompt)
        
        # Extract content if response is AIMessage (from ChatHuggingFace)
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        # Clean potential markdown wrappers
        clean_text = response_text.replace("```markdown", "").replace("```", "").strip()
        
        # If response is too short, add a note
        if len(clean_text) < 200:
            clean_text += "\n\n*Note: For more detailed information, please refer to your course materials or ask specific questions in the chat.*"
        
        # Append sources reference section
        if sources_list:
            clean_text += "\n\n---\n\n### 📚 References\n\n"
            for idx, src in enumerate(sources_list, 1):
                clean_text += f"{idx}. **{src['filename']}**, page {src['page']}\n"
        
        return clean_text
    except Exception as e:
        return f"### Error Generating Lesson\nCould not retrieve content: {e}"


def query_knowledge_base(question: str, history: list = []):

    
    # Init
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=get_embeddings()
    )
    llm = get_llm()
    
    # 1. Search
    docs = vector_store.similarity_search(question, k=3)
    context = "\n".join([d.page_content[:500] for d in docs])
    
    # 2. Format History
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    
    # 3. Prompt
    prompt = f"""
    Context: {context}
    Chat History:
    {history_text}
    
    User Question: {question}
    
    TASK: Answer the user's question based on the context.
    If you don't know, say "I don't know".
    """
    
    res = llm.invoke(prompt)
    
    # Extract content if response is AIMessage
    if hasattr(res, 'content'):
        answer_text = res.content
    else:
        answer_text = str(res)
    
    # Return source metadata
    sources_list = []
    for d in docs:
        meta = d.metadata
        sources_list.append({"source": meta.get("source", "Unknown"), "page": meta.get("page", 1)})
        
    return {
        "answer": answer_text,
        "sources": sources_list
    }
def generate_quiz_data(topic_title: str):

    
    # Initialize resources
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=get_embeddings()
    )
    llm = get_llm()

    # 1. Search Context
    docs = vector_store.similarity_search(topic_title, k=3)
    context_text = "\n".join([d.page_content[:300] for d in docs])
    
    # Helper: Generate realistic fallback quiz from context
    def create_context_based_fallback():
        """Generate realistic quiz questions from context when LLM fails"""
        # Extract key terms and concepts from context
        sentences = context_text.split('.')
        key_concepts = []
        for sentence in sentences[:10]:  # Look at first 10 sentences
            words = sentence.strip().split()
            if len(words) > 3:
                key_concepts.append(sentence.strip())
        
        if not key_concepts or len(key_concepts) < 3:
            # Ultimate fallback if no context
            return [
                {
                    "question": f"Which statement best describes {topic_title}?",
                    "options": [
                        "A core concept that requires understanding of fundamentals",
                        "An advanced technique used in specialized applications",
                        "A theoretical framework with practical implementations"
                    ],
                    "answer": "A core concept that requires understanding of fundamentals"
                },
                {
                    "question": f"What is the primary purpose of {topic_title}?",
                    "options": [
                        "To optimize performance and efficiency",
                        "To provide structure and organization",
                        "To enable complex problem solving"
                    ],
                    "answer": "To provide structure and organization"
                },
                {
                    "question": f"When should you apply {topic_title}?",
                    "options": [
                        "When dealing with large-scale systems",
                        "During the initial design phase",
                        "When specific requirements are identified"
                    ],
                    "answer": "When specific requirements are identified"
                }
            ]
        
        # Generate questions from extracted concepts
        fallback_quiz = []
        for i, concept in enumerate(key_concepts[:3]):
            # Create slight variations of the concept as distractors
            words = concept.split()
            if len(words) > 5:
                # Create plausible wrong answers by modifying the concept
                correct_answer = ' '.join(words[:15])  # First part as correct
                distractor1 = ' '.join(words[2:10] + words[:2]) if len(words) > 10 else "Alternative interpretation of the concept"
                distractor2 = ' '.join(words[5:15]) if len(words) > 15 else "Related but distinct concept"
                
                fallback_quiz.append({
                    "question": f"Regarding {topic_title}, which statement is most accurate?",
                    "options": [correct_answer, distractor1, distractor2],
                    "answer": correct_answer
                })
        
        while len(fallback_quiz) < 3:
            fallback_quiz.append({
                "question": f"What is an important aspect of {topic_title}?",
                "options": [
                    "Understanding the underlying principles",
                    "Memorizing specific implementation details",
                    "Following standard industry practices"
                ],
                "answer": "Understanding the underlying principles"
            })
        
        return fallback_quiz[:3]
    
    # 2. Enhanced prompt for realistic quiz questions
    prompt = f"""Create 3 challenging multiple choice questions about: {topic_title}

Context: {context_text}

CRITICAL REQUIREMENTS for answer choices:
1. Make wrong answers (distractors) PLAUSIBLE and REALISTIC
2. Use common misconceptions as wrong answers
3. Make distractors similar enough that students need real understanding to choose correctly
4. Avoid obviously wrong or silly options like "Option A", "Option B"
5. Base all options on the actual context provided

Example of GOOD distractors (realistic and plausible):
Q: "What is encapsulation in OOP?"
- "Hiding implementation details and exposing only necessary interfaces" [CORRECT]
- "Combining data and methods that operate on that data into a single unit" [PLAUSIBLE - related to OOP but describes a class]
- "The ability of objects to take multiple forms through inheritance" [PLAUSIBLE - actually polymorphism]

Example of BAD distractors (too obvious):
- "A type of loop"
- "Option A"
- "None of the above"

Output as JSON array with 3 questions:
[
  {{
    "question": "Specific question text?",
    "options": ["Realistic wrong answer 1", "Correct answer", "Realistic wrong answer 2"],
    "answer": "Correct answer"
  }},
  ... (2 more questions)
]

JSON:"""
    
    try:
        response = llm.invoke(prompt)
        
        # Extract content if response is AIMessage
        if hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        import json
        quiz_data = json.loads(clean_json)
        
        # Ensure it's a list
        if not isinstance(quiz_data, list):
            raise ValueError("Quiz data must be a list")
        
        # POST-PROCESSING: Ensure exactly 3 questions
        if len(quiz_data) < 3:

            context_fallback = create_context_based_fallback()
            # Add missing questions from fallback
            questions_needed = 3 - len(quiz_data)
            quiz_data.extend(context_fallback[:questions_needed])
        elif len(quiz_data) > 3:
            quiz_data = quiz_data[:3]  # Trim to exactly 3
        
        return quiz_data
        
    except Exception as e:

        # Return context-based fallback instead of generic placeholders
        return create_context_based_fallback()