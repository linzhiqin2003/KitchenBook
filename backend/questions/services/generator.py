"""
DeepSeek API integration for question generation.
Supports multi-course system with standardized question generation.
"""
import os
import json
import random
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from .parser import parse_courseware, parse_simulation_questions, infer_topic, get_all_topics
from .courses import get_course, get_default_course

# Load .env from backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com/v1"


def get_client():
    """Initialize OpenAI-compatible client for DeepSeek."""
    if not API_KEY:
        return None
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def generate_question(seed_question, course_id=None, context_data=None, target_difficulty=None):
    """
    Generate a new question based on a seed question and courseware context.
    
    Args:
        seed_question: A sample question to use as reference for style/difficulty
        course_id: Course identifier (uses default if None)
        context_data: Pre-loaded courseware context (loaded if None)
        target_difficulty: Specific difficulty to generate ('easy', 'medium', 'hard') or None for auto
    
    Returns:
        dict with question, options, answer, explanation, or error
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}
    
    if course_id is None:
        course_id = get_default_course()
    
    if context_data is None:
        context_data = parse_courseware(course_id)
    
    # Get course info for customized prompts
    course_config = get_course(course_id)
    course_name = course_config.get("name", "Course") if course_config else "Course"
    
    topics = list(context_data.keys())
    topic = infer_topic(seed_question, topics, course_id)
    
    # Get a larger context for more material to draw from (randomly sampled if too large)
    full_text = context_data.get(topic, "")
    if len(full_text) > 50000:
        start_idx = random.randint(0, len(full_text) - 50000)
        context_snippet = full_text[start_idx : start_idx + 50000]
    else:
        context_snippet = full_text
    
    prompt = f"""You are an expert university exam question designer for a "{course_name}" course.

## Your Goal
Create an **original, creative multiple-choice question** that tests a knowledge point from the provided Course Material. 
The question should be **inspired by** but **NOT a copy of** the Reference Question.

## Key Requirements
1. **Focus on the Course Material**: Your question MUST test a concept, command, or technique that appears in the Course Material below. Do NOT just rephrase the Reference Question.
2. **Be Creative & Divergent**: 
   - Pick a DIFFERENT specific detail, flag, scenario, or edge case from the Course Material.
   - Create a realistic scenario (e.g., "Alice is trying to...", "A developer wants to...").
   - Test practical understanding, not just memorization.
3. **Difficulty**: {f'Generate a **{target_difficulty.upper()}** difficulty question.' if target_difficulty else 'Rate your question as "easy", "medium", or "hard":'}
   - **easy**: Basic concept recall, straightforward application
   - **medium**: Requires understanding multiple concepts or common edge cases
   - **hard**: Complex scenarios, subtle distinctions, or advanced topics
4. **Four Options**: Provide exactly 4 plausible options (A, B, C, D). Include common misconceptions as distractors.
5. **Detailed Explanation**: Explain why the correct answer is right AND why each wrong option is incorrect.

## Output Format (JSON only)
{{
  "topic": "{topic}",
  "difficulty": "easy" or "medium" or "hard",
  "question": "A scenario-based question text...",
  "options": ["A. Option", "B. Option", "C. Option", "D. Option"],
  "answer": "A. The full correct option text",
  "explanation": "Detailed explanation covering all options..."
}}

**IMPORTANT: Code Formatting**
If any option contains code (e.g., function definitions, shell commands, SQL queries), you MUST preserve code formatting with proper newlines (`\n`) and indentation. For example:
- WRONG: `"A. char* foo() {{ int x = 1; return x; }}"`
- CORRECT: `"A. char* foo() {{\n    int x = 1;\n    return x;\n}}"`

---
## Reference Question (for difficulty/style reference ONLY, do NOT copy):
{seed_question}

---
## Course Material ({topic}) - USE THIS TO CREATE YOUR QUESTION:
{context_snippet}
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an expert exam question designer. Output ONLY valid JSON. Be creative and divergent."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.9  # Higher temperature for more creativity
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        result["course_id"] = course_id
        # Use target difficulty if specified, otherwise validate AI's choice
        if target_difficulty and target_difficulty in ["easy", "medium", "hard"]:
            result["difficulty"] = target_difficulty
        elif result.get("difficulty") not in ["easy", "medium", "hard"]:
            result["difficulty"] = "medium"  # Default to medium if invalid
        return result
    except Exception as e:
        return {"error": str(e)}



def generate_question_for_topic(topic, course_id=None, context_data=None, target_difficulty=None):
    """
    Generate a new question for a specific topic.
    Used when user selects topic-based practice mode.
    
    Args:
        topic: Topic name to generate question for
        course_id: Course identifier (uses default if None)
        context_data: Pre-loaded courseware context (loaded if None)
        target_difficulty: Specific difficulty ('easy', 'medium', 'hard') or None for auto
    
    Returns:
        dict with question, options, answer, explanation, or error
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}
    
    if course_id is None:
        course_id = get_default_course()
    
    if context_data is None:
        context_data = parse_courseware(course_id)
    
    # Get course info for customized prompts
    course_config = get_course(course_id)
    course_name = course_config.get("name", "Course") if course_config else "Course"
    
    # Find the best matching topic key
    matching_topic = None
    for key in context_data.keys():
        if topic.lower() in key.lower() or key.lower() in topic.lower():
            matching_topic = key
            break
    
    if not matching_topic:
        # Try partial match
        for key in context_data.keys():
            if any(part in key.lower() for part in topic.lower().split('-')):
                matching_topic = key
                break
    
    if not matching_topic and context_data:
        # Fallback to first available topic
        matching_topic = list(context_data.keys())[0]
    
    full_text = context_data.get(matching_topic, "")
    if len(full_text) > 50000:
        start_idx = random.randint(0, len(full_text) - 50000)
        context_snippet = full_text[start_idx : start_idx + 50000]
    else:
        context_snippet = full_text
    
    prompt = f"""You are an expert university exam question designer for a "{course_name}" course.

## Your Goal
Create an **original, creative multiple-choice question** that tests a knowledge point from the provided Course Material for the topic "{matching_topic}".

## Key Requirements
1. **Focus on the Course Material**: Your question MUST test a concept, command, or technique that appears in the Course Material below.
2. **Be Creative & Divergent**: 
   - Pick a specific detail, flag, scenario, or edge case from the Course Material.
   - Create a realistic scenario (e.g., "Alice is trying to...", "A developer wants to...").
   - Test practical understanding, not just memorization.
3. **Difficulty**: {f"Generate a **{target_difficulty.upper()}** difficulty question." if target_difficulty else "Undergraduate exam level (medium difficulty)."}
   - **easy**: Basic concept recall, straightforward application
   - **medium**: Requires understanding multiple concepts or common edge cases
   - **hard**: Complex scenarios, subtle distinctions, or advanced topics
4. **Four Options**: Provide exactly 4 plausible options (A, B, C, D). Include common misconceptions as distractors.
5. **Detailed Explanation**: Explain why the correct answer is right AND why each wrong option is incorrect.

## Output Format (JSON only)
{{
  "topic": "{matching_topic}",
  "difficulty": "easy" or "medium" or "hard",
  "question": "A scenario-based question text...",
  "options": ["A. Option", "B. Option", "C. Option", "D. Option"],
  "answer": "A. The full correct option text",
  "explanation": "Detailed explanation covering all options..."
}}

**IMPORTANT: Code Formatting**
If any option contains code (e.g., function definitions, shell commands, SQL queries), you MUST preserve code formatting with proper newlines (`\n`) and indentation. For example:
- WRONG: `"A. char* foo() {{ int x = 1; return x; }}"`
- CORRECT: `"A. char* foo() {{\n    int x = 1;\n    return x;\n}}"`

---
## Course Material ({matching_topic}) - USE THIS TO CREATE YOUR QUESTION:
{context_snippet}
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are an expert exam question designer. Output ONLY valid JSON. Be creative and divergent."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.9  # Higher temperature for more creativity
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        result["seed_question"] = f"Topic: {matching_topic}"
        result["course_id"] = course_id
        # Use target difficulty if specified
        if target_difficulty and target_difficulty in ["easy", "medium", "hard"]:
            result["difficulty"] = target_difficulty
        elif result.get("difficulty") not in ["easy", "medium", "hard"]:
            result["difficulty"] = "medium"
        return result
    except Exception as e:
        return {"error": str(e)}


def batch_generate(course_id=None, limit=None):
    """
    Generate questions from all seed questions for a course.
    
    Args:
        course_id: Course identifier (uses default if None)
        limit: Maximum number of questions to generate
    
    Returns:
        list of generated question dicts
    """
    if course_id is None:
        course_id = get_default_course()
    
    seeds = parse_simulation_questions(course_id)
    context = parse_courseware(course_id)
    
    if limit:
        seeds = seeds[:limit]
    
    results = []
    for seed in seeds:
        result = generate_question(seed, course_id, context)
        if "error" not in result:
            result["seed_question"] = seed
            results.append(result)
    
    return results
