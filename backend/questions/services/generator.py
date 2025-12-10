"""
DeepSeek API integration for question generation.
"""
import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from .parser import parse_courseware, parse_courseware_with_sources, parse_simulation_questions, infer_topic

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


def generate_question(seed_question, context_data=None):
    """
    Generate a new question based on a seed question and courseware context.
    Returns dict with question, options, answer, explanation, and source references.
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}
    
    # Use source-tracking version for better citations
    if context_data is None:
        context_data = parse_courseware_with_sources()
    
    topics = list(context_data.keys())
    topic = infer_topic(seed_question, topics)
    
    # Get context with source information
    topic_data = context_data.get(topic, {})
    if isinstance(topic_data, dict):
        topic_content = topic_data.get("content", "")
        source_list = topic_data.get("source_list", "")
    else:
        # Fallback for old format
        topic_content = topic_data
        source_list = ""
    
    # Truncate if too long
    if len(topic_content) > 50000:
        context_snippet = topic_content[:50000]
    else:
        context_snippet = topic_content
    
    prompt = f"""You are an expert university exam question designer for a "Software Tools" course.

## Your Goal
Create an **original, creative multiple-choice question** that tests a knowledge point from the provided Course Material. 
The question should be **inspired by** but **NOT a copy of** the Reference Question.

## Key Requirements
1. **Focus on the Course Material**: Your question MUST test a concept, command, or technique that appears in the Course Material below. Do NOT just rephrase the Reference Question.
2. **Be Creative & Divergent**: 
   - Pick a DIFFERENT specific detail, flag, scenario, or edge case from the Course Material.
   - Create a realistic scenario (e.g., "Alice is trying to...", "A developer wants to...").
   - Test practical understanding, not just memorization.
3. **Difficulty**: Match the Reference Question's difficulty level (undergraduate exam level).
4. **Four Options**: Provide exactly 4 plausible options (A, B, C, D). Include common misconceptions as distractors.
5. **Detailed Explanation with Source Reference**: 
   - Explain why the correct answer is right AND why each wrong option is incorrect.
   - **IMPORTANT**: At the end of the explanation, add a "📚 Source" section citing which specific courseware file(s) this knowledge comes from.
   - Look for "=== SOURCE: xxx ===" markers in the Course Material to identify file names.

## Output Format (JSON only)
{{
  "topic": "{topic}",
  "question": "A scenario-based question text...",
  "options": ["A. Option", "B. Option", "C. Option", "D. Option"],
  "answer": "A. The full correct option text",
  "explanation": "Detailed explanation covering all options...\\n\\n📚 **Source**: [filename.md] - [specific section or concept referenced]",
  "source_files": ["list of source files used, e.g., 'slides.md', 'lab/README.md'"]
}}

---
## Available Source Files for {topic}:
{source_list}

---
## Reference Question (for difficulty/style reference ONLY, do NOT copy):
{seed_question}

---
## Course Material ({topic}) - USE THIS TO CREATE YOUR QUESTION:
{context_snippet}
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": "You are an expert exam question designer. Output ONLY valid JSON. Be creative and divergent. Always cite source files in your explanation."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.9  # Higher temperature for more creativity
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}


def generate_question_for_topic(topic_name, context_data=None):
    """
    Generate a question for a specific topic directly from courseware.
    No seed question required - creates original questions based on topic material.
    
    Args:
        topic_name: The topic to generate for (e.g., 'git', 'sql', 'regex')
        context_data: Optional pre-parsed courseware data (with sources)
    
    Returns:
        dict with question, options, answer, explanation, and source references
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}
    
    # Use source-tracking version for better citations
    if context_data is None:
        context_data = parse_courseware_with_sources()
    
    # Find matching topic (case-insensitive partial match)
    matched_topic = None
    for available_topic in context_data.keys():
        if topic_name.lower() in available_topic.lower():
            matched_topic = available_topic
            break
    
    if not matched_topic:
        # If no exact match, try to use the topic_name directly
        matched_topic = topic_name
        if matched_topic not in context_data:
            return {"error": f"Topic '{topic_name}' not found in courseware"}
    
    # Get context with source information
    topic_data = context_data.get(matched_topic, {})
    if isinstance(topic_data, dict):
        topic_content = topic_data.get("content", "")
        source_list = topic_data.get("source_list", "")
    else:
        # Fallback for old format
        topic_content = topic_data
        source_list = ""
    
    # Truncate if too long
    if len(topic_content) > 50000:
        context_snippet = topic_content[:50000]
    else:
        context_snippet = topic_content
    
    if not context_snippet:
        return {"error": f"No content available for topic '{topic_name}'"}
    
    prompt = f"""You are an expert university exam question designer for a "Software Tools" course.

## Your Goal
Create an **original, creative multiple-choice question** specifically about **{matched_topic}**.
The question should test practical knowledge from the provided Course Material.

## Key Requirements
1. **Focus on {matched_topic}**: Your question MUST test a concept, command, or technique specifically related to {matched_topic} from the Course Material.
2. **Be Creative & Practical**: 
   - Pick a specific detail, flag, scenario, or edge case from the Course Material.
   - Create a realistic scenario (e.g., "Alice is trying to...", "A developer wants to...").
   - Test practical understanding, not just memorization.
3. **Difficulty**: Undergraduate exam level - challenging but fair.
4. **Four Options**: Provide exactly 4 plausible options (A, B, C, D). Include common misconceptions as distractors.
5. **Detailed Explanation with Source Reference**: 
   - Explain why the correct answer is right AND why each wrong option is incorrect.
   - **IMPORTANT**: At the end of the explanation, add a "📚 Source" section citing which specific courseware file(s) this knowledge comes from.
   - Look for "=== SOURCE: xxx ===" markers in the Course Material to identify file names.

## Output Format (JSON only)
{{
  "topic": "{matched_topic}",
  "question": "A scenario-based question text about {matched_topic}...",
  "options": ["A. Option", "B. Option", "C. Option", "D. Option"],
  "answer": "A. The full correct option text",
  "explanation": "Detailed explanation covering all options...\\n\\n📚 **Source**: [filename.md] - [specific section or concept referenced]",
  "source_files": ["list of source files used, e.g., 'slides.md', 'lab/README.md'"]
}}

---
## Available Source Files for {matched_topic}:
{source_list}

---
## Course Material ({matched_topic}) - USE THIS TO CREATE YOUR QUESTION:
{context_snippet}
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": f"You are an expert exam question designer specializing in {matched_topic}. Output ONLY valid JSON. Be creative and test practical knowledge. Always cite source files in your explanation."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.9
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        result["seed_question"] = f"topic:{topic_name}"
        return result
    except Exception as e:
        return {"error": str(e)}



def batch_generate(limit=None):
    """
    Generate questions from all seed questions.
    Returns list of generated question dicts.
    """
    seeds = parse_simulation_questions()
    context = parse_courseware()
    
    if limit:
        seeds = seeds[:limit]
    
    results = []
    for seed in seeds:
        result = generate_question(seed, context)
        if "error" not in result:
            result["seed_question"] = seed
            results.append(result)
    
    return results

