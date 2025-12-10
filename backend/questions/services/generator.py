"""
DeepSeek API integration for question generation.
"""
import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from .parser import parse_courseware, parse_simulation_questions, infer_topic

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
    Returns dict with question, options, answer, explanation.
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}
    
    if context_data is None:
        context_data = parse_courseware()
    
    topics = list(context_data.keys())
    topic = infer_topic(seed_question, topics)
    
    # Get a larger context for more material to draw from
    if len(context_data.get(topic, "")) > 20000:
        context_snippet = context_data.get(topic, "")[:20000]
    else:
        context_snippet = context_data.get(topic, "")
    
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
5. **Detailed Explanation**: Explain why the correct answer is right AND why each wrong option is incorrect.

## Output Format (JSON only)
{{
  "topic": "{topic}",
  "question": "A scenario-based question text...",
  "options": ["A. Option", "B. Option", "C. Option", "D. Option"],
  "answer": "A. The full correct option text",
  "explanation": "Detailed explanation covering all options..."
}}

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
                {"role": "system", "content": "You are an expert exam question designer. Output ONLY valid JSON. Be creative and divergent."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.9  # Higher temperature for more creativity
        )
        content = response.choices[0].message.content
        return json.loads(content)
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
