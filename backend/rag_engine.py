import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from backend.config import get_llm_provider, get_llm_config, LLMProvider

CACHE_DIR = "./chroma_db"

def get_llm():
    """
    Get LLM instance based on environment configuration.
    Supports both local (Ollama) and cloud (Hugging Face) modes.
    """
    provider = get_llm_provider()
    config = get_llm_config()
    
    if provider == LLMProvider.OLLAMA:
        # Local mode - uses Ollama for offline inference
        return Ollama(
            model=config["model"],
            base_url=config.get("base_url", "http://localhost:11434")
        )
    else:
        # Cloud mode - uses Hugging Face Inference API
        from langchain_huggingface import HuggingFaceEndpoint
        return HuggingFaceEndpoint(
            repo_id=config["model"],
            huggingfacehub_api_token=config["api_token"],
            max_length=config.get("max_length", 512),
            temperature=config.get("temperature", 0.7),
            task="text-generation"
        )


def ingest_document(file_path: str):
    """
    Ingests a PDF document into the vector database.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Load PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # Split text
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    
    # Store in ChromaDB
    # Note: Chroma will automatically persist to disk in newer versions when persist_directory is set
    Chroma.from_documents(
        documents=splits,
        embedding=OllamaEmbeddings(model="nomic-embed-text"),
        persist_directory=CACHE_DIR
    )
    # Ingestion successful

def ingest_url(url: str):
    """
    Ingests content from a URL (YouTube or Web).
    """
    from langchain_community.document_loaders import YoutubeLoader, WebBaseLoader
    
    docs = []
    try:
        if "youtube.com" in url or "youtu.be" in url:

            try:
                # Try with metadata first (requires pytube, often flaky)
                loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
                docs = loader.load()
            except Exception as e:

                # Fallback: Transcript only (no title/author)
                loader = YoutubeLoader.from_youtube_url(url, add_video_info=False)
                docs = loader.load()
        else:

            loader = WebBaseLoader(url)
            docs = loader.load()
            
        # Generic processing
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = splitter.split_documents(docs)
        
        if not splits:
            raise ValueError("No content found to ingest")
            
        # Store in ChromaDB
        Chroma.from_documents(
            documents=splits,
            embedding=OllamaEmbeddings(model="nomic-embed-text"),
            persist_directory=CACHE_DIR
        )
        
        title = docs[0].metadata.get("title", url) if docs else url

        return title
        
    except Exception as e:
        print(f"Error ingesting URL: {e}")
        raise e

def delete_document(source_path: str):
    """
    Removes a document from the vector database by its source path.
    """
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
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
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
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
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
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
        # Clean potential markdown wrappers
        clean_text = response.replace("```markdown", "").replace("```", "").strip()
        
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
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
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
    
    # Return source metadata
    sources_list = []
    for d in docs:
        meta = d.metadata
        sources_list.append({"source": meta.get("source", "Unknown"), "page": meta.get("page", 1)})
        
    return {
        "answer": res,
        "sources": sources_list
    }
def generate_quiz_data(topic_title: str):

    
    # Initialize resources
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
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
        clean_json = response.replace("```json", "").replace("```", "").strip()
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