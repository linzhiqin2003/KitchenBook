"""
Standardized Markdown parser for courseware and simulation questions.
Works with the multi-course system defined in courses.py.
"""
import os
import re
import glob
from pathlib import Path
from .courses import get_course, get_courseware_path, get_simulation_path, get_topic_keywords, get_default_course


def parse_simulation_questions(course_id=None):
    """
    Extract questions from all simulation files for a course.
    Returns list of question text blocks.
    
    Args:
        course_id: Course identifier (e.g., 'software-tools', 'c-programming')
                  If None, uses the default course.
    """
    if course_id is None:
        course_id = get_default_course()
    
    if course_id is None:
        return []
    
    simulation_dir = get_simulation_path(course_id)
    
    if not simulation_dir.exists():
        return []
    
    questions = []
    
    # Find all markdown files in the simulation directory
    md_files = glob.glob(str(simulation_dir / "*.md"))
    
    for file_path in md_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract questions using multiple patterns to be flexible
            file_questions = extract_questions_from_content(content)
            questions.extend(file_questions)
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            continue
    
    return questions


def extract_questions_from_content(content):
    """
    Extract individual questions from markdown content.
    Supports multiple question formats:
    - Q1. ... Q2. ...
    - 1. ... 2. ...
    """
    questions = []
    
    # Pattern 1: Q{number}. format (e.g., "Q1. Which of the following...")
    pattern1 = re.compile(r'(Q\d+\..*?)(?=Q\d+\.|## 第\d+页|Page \d+|END OF|$)', re.DOTALL)
    matches1 = pattern1.findall(content)
    
    # Pattern 2: {number}. format (e.g., "1. Which of the following...")
    # More careful pattern to avoid matching sub-items
    pattern2 = re.compile(r'(?:^|\n)(\d+\.\s+[A-Z].*?)(?=\n\d+\.\s+[A-Z]|## 第\d+页|Page \d+|END OF|$)', re.DOTALL)
    matches2 = pattern2.findall(content)
    
    # Combine and deduplicate
    all_matches = matches1 + matches2
    
    for match in all_matches:
        clean_text = match.strip()
        
        # Validate it looks like a multiple-choice question
        # Must have at least options A and B
        has_options = (
            ("A." in clean_text and "B." in clean_text) or
            ("a)" in clean_text.lower() and "b)" in clean_text.lower()) or
            ("(A)" in clean_text and "(B)" in clean_text)
        )
        
        if has_options and len(clean_text) > 50:  # Minimum length check
            questions.append(clean_text)
    
    return questions


def parse_courseware(course_id=None):
    """
    Read all markdown files from courseware directory.
    Returns dict: {topic_name: concatenated_content}
    
    Args:
        course_id: Course identifier. If None, uses the default course.
    """
    if course_id is None:
        course_id = get_default_course()
    
    if course_id is None:
        return {}
    
    courseware_dir = get_courseware_path(course_id)
    
    if not courseware_dir.exists():
        return {}
    
    context_by_topic = {}
    
    # Check if courseware is organized in subdirectories or flat
    subdirs = [d for d in courseware_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if subdirs:
        # Subdirectory structure (e.g., 01-sysadmin, 02-fundamentals)
        for subdir in subdirs:
            # Extract topic name: "01-sysadmin" -> "sysadmin", "A_Basics" -> "Basics"
            topic = extract_topic_name(subdir.name)
            
            topic_content = []
            md_files = glob.glob(str(subdir / "**/*.md"), recursive=True)
            
            for md_file in md_files:
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        topic_content.append(f.read())
                except Exception:
                    pass
            
            if topic_content:
                context_by_topic[topic] = "\n\n---\n\n".join(topic_content)
    else:
        # Flat structure - group by filename or treat each file as a topic
        md_files = glob.glob(str(courseware_dir / "*.md"))
        
        for md_file in md_files:
            filename = Path(md_file).stem
            topic = extract_topic_name(filename)
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    context_by_topic[topic] = f.read()
            except Exception:
                pass
    
    return context_by_topic


def extract_topic_name(raw_name):
    """
    Extract a clean topic name from directory or file name.
    Examples:
    - "01-sysadmin" -> "sysadmin"
    - "A_Preamble" -> "Preamble"
    - "K_Pointers" -> "Pointers"
    - "fundamentals" -> "fundamentals"
    """
    # Remove leading number and separator: "01-topic" or "01_topic"
    match = re.search(r'^\d+[-_](.+)$', raw_name)
    if match:
        return match.group(1).lower().replace('_', '-')
    
    # Remove leading letter and separator: "A_Topic" or "A-Topic"
    match = re.search(r'^[A-Z][-_](.+)$', raw_name)
    if match:
        return match.group(1).lower().replace('_', '-')
    
    # Just clean up the name
    return raw_name.lower().replace('_', '-')


def infer_topic(question_text, topics, course_id=None):
    """
    Infer the topic of a question using AI (DeepSeek).
    Falls back to keyword matching if AI call fails.
    
    Args:
        question_text: The question text to analyze
        topics: List of available topics
        course_id: Course identifier for course-specific context
    """
    if not topics:
        return 'general'
    
    # Try AI-based inference first
    ai_result = infer_topic_with_ai(question_text, topics, course_id)
    if ai_result:
        return ai_result
    
    # Fallback to keyword-based inference
    return infer_topic_keyword_based(question_text, topics, course_id)


def infer_topic_with_ai(question_text, topics, course_id=None):
    """
    Use DeepSeek AI to classify the topic of a question.
    Returns None if API call fails.
    """
    import os
    import json
    from pathlib import Path
    from openai import OpenAI
    from dotenv import load_dotenv
    
    # Load API key
    BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
    load_dotenv(BACKEND_DIR / ".env")
    
    API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not API_KEY:
        return None
    
    try:
        client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com/v1")
        
        # Get course name for context
        course_config = get_course(course_id) if course_id else None
        course_name = course_config.get("name", "Course") if course_config else "Course"
        
        # Format topics list
        topics_list = "\n".join([f"- {t}" for t in topics])
        
        prompt = f"""You are a teaching assistant for a "{course_name}" course.

Given the following exam question, classify it into ONE of the available topics.

## Question:
{question_text[:1500]}

## Available Topics:
{topics_list}

## Instructions:
- Analyze the question content, code snippets, and concepts mentioned
- Choose the SINGLE most relevant topic from the list
- If unsure, pick the closest match
- Return ONLY the topic name exactly as listed, nothing else

## Your Answer (topic name only):"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a precise classifier. Output ONLY the topic name, no explanation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.1  # Low temperature for consistent classification
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        # Validate result is in topics list
        for topic in topics:
            if topic.lower() == result or result in topic.lower() or topic.lower() in result:
                return topic
        
        # Try partial match
        for topic in topics:
            if any(word in result for word in topic.split('-') if len(word) > 3):
                return topic
        
        return None
        
    except Exception as e:
        print(f"AI topic inference failed: {e}")
        return None


def infer_topic_keyword_based(question_text, topics, course_id=None):
    """
    Fallback: Infer the topic of a question using keyword matching.
    Uses course-specific keywords if available.
    """
    question_lower = question_text.lower()
    
    # Get course-specific keywords
    topic_keywords = {}
    if course_id:
        topic_keywords = get_topic_keywords(course_id)
    
    scores = {t: 0 for t in topics}
    
    for topic in topics:
        # Direct topic name match
        topic_clean = topic.lower().replace('-', ' ').replace('_', ' ')
        if topic_clean in question_lower:
            scores[topic] += 3
        
        # Keyword matching from course config
        normalized_topic = topic.lower().replace('_', '-')
        if normalized_topic in topic_keywords:
            for kw in topic_keywords[normalized_topic]:
                if kw.lower() in question_lower:
                    scores[topic] += 2
        
        # Partial topic name match
        for word in topic.split('-'):
            if len(word) > 3 and word.lower() in question_lower:
                scores[topic] += 1
    
    # Return best matching topic
    best_topic = max(scores, key=scores.get) if scores else topics[0]
    return best_topic if scores.get(best_topic, 0) > 0 else topics[0]


def get_all_topics(course_id=None):
    """
    Get all available topics for a course.
    Combines courseware topics with keyword-defined topics.
    """
    courseware_topics = list(parse_courseware(course_id).keys())
    
    keyword_topics = []
    if course_id:
        keyword_topics = list(get_topic_keywords(course_id).keys())
    
    # Combine and deduplicate
    all_topics = list(set(courseware_topics + keyword_topics))
    all_topics.sort()
    
    return all_topics
