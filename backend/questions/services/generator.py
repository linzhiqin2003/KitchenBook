"""
DeepSeek API integration for question generation.
Supports multi-course system with standardized question generation.
"""
import os
import json
import random
from pathlib import Path
from dotenv import load_dotenv
from common.deepseek_models import CHAT_MODEL, get_client as _get_deepseek_client, non_thinking_kwargs
from .parser import parse_courseware, parse_simulation_questions, infer_topic, get_all_topics
from .courses import get_course, get_default_course

# Load .env from backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

API_KEY = os.getenv("DEEPSEEK_API_KEY")


def get_client():
    """Initialize OpenAI-compatible client for DeepSeek."""
    return _get_deepseek_client(API_KEY)


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
Create an **original MULTIPLE-CHOICE question** following these principles:
1. **Knowledge**: Test a concept/knowledge point from the **Course Material** provided below
2. **Style**: Learn from the Reference Question's topic/difficulty, but ALWAYS output a multiple-choice format
3. **Originality**: Create a NEW question, not a copy of the reference

## IMPORTANT: Output Format is Strictly Multiple-Choice
**The Reference Question may be in ANY format (fill-in-the-blank, short answer, etc.), but YOUR output MUST be a multiple-choice question with exactly 4 options (A, B, C, D).**

The Reference Question is only for understanding the topic and difficulty level. Create an entirely new multiple-choice question based on the Course Material.

## CRITICAL: Self-Contained Questions for Closed-Book Exam
**This is a CLOSED-BOOK exam. The question must be completely self-contained.**

- The **knowledge tested** MUST come from the Course Material
- But the **question text** must NOT reference external materials
- Include ALL necessary information (code, data, context) directly in the question

**DO NOT write**:
- "According to the lecture material..."
- "As shown in the slides..."
- "Referring to the course notes..."

**INSTEAD write**:
- "Given the following code: [code], what is the output?"
- "Consider a hash table that uses linear probing..."
- "A developer is debugging a program that..."

## Key Requirements
1. **Knowledge Source**: Extract a specific concept, rule, or technique from the Course Material below. The question MUST accurately test this knowledge.
2. **Four Options (A, B, C, D)**: ALWAYS provide exactly 4 plausible options. Include common misconceptions as distractors.
3. **Difficulty**: {f'Generate a **{target_difficulty.upper()}** difficulty question.' if target_difficulty else 'Rate your question as "easy", "medium", or "hard":'}
   - **easy**: Basic concept recall, straightforward application
   - **medium**: Requires understanding multiple concepts or common edge cases
   - **hard**: Complex scenarios, subtle distinctions, or advanced topics
4. **Four Options**: Provide exactly 4 plausible options (A, B, C, D). Include common misconceptions as distractors.
5. **Detailed Explanation**: Explain why the correct answer is right AND why each wrong option is incorrect.
6. **Citation (REQUIRED)**: Cite the exact section / passage of the Course Material below that justifies the answer.

## Output Format (JSON only)
{{
  "topic": "{topic}",
  "difficulty": "easy" or "medium" or "hard",
  "question": "A scenario-based question text...",
  "options": ["A. Option", "B. Option", "C. Option", "D. Option"],
  "answer": "A. The full correct option text",
  "explanation": "Detailed explanation covering all options...",
  "source_chapter": "Section / sub-heading of the course material that the answer comes from (e.g. 'L4. UML Class Diagrams § Aggregation')",
  "source_excerpt": "A short verbatim quote from the Course Material (≤140 chars) that proves the answer."
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
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert exam question designer. Output ONLY valid JSON. Be creative and divergent."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.9,  # Higher temperature for more creativity
            **non_thinking_kwargs(),
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



def generate_question_for_topic(topic, course_id=None, context_data=None, target_difficulty=None, seed_question=None):
    """
    Generate a new question for a specific topic.
    Used when user selects topic-based practice mode.

    Args:
        topic: Topic name to generate question for
        course_id: Course identifier (uses default if None)
        context_data: Pre-loaded courseware context (loaded if None)
        target_difficulty: Specific difficulty ('easy', 'medium', 'hard') or None for auto
        seed_question: Optional reference question (e.g. sampled from the mock paper)
            used purely for style/difficulty calibration. When provided, it's added
            as a "Reference Question" section in the prompt — the LLM is instructed
            NOT to copy it.
    
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
    
    # 1. Try exact match first (case-insensitive)
    for key in context_data.keys():
        if topic.lower() == key.lower():
            matching_topic = key
            break
    
    # 2. If no exact match, try if topic is a suffix of a key (e.g., "strings" matches "i-strings" but not "huffman-strings")
    if not matching_topic:
        for key in context_data.keys():
            # Check if key ends with the topic (after a hyphen)
            if key.lower().endswith('-' + topic.lower()) or key.lower() == topic.lower():
                matching_topic = key
                break
    
    # 3. Last resort: partial match (but prefer shorter keys)
    if not matching_topic:
        candidates = []
        for key in context_data.keys():
            if topic.lower() in key.lower() or key.lower() in topic.lower():
                candidates.append(key)
        if candidates:
            # Prefer the shortest matching key (more specific)
            matching_topic = min(candidates, key=len)
    
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
Create an **original multiple-choice question** for the topic "{matching_topic}" following these principles:
1. **Knowledge**: Test a concept/knowledge point from the **Course Material** provided below
2. **Originality**: Create a NEW, creative question - not a copy of any existing question

## CRITICAL: Self-Contained Questions for Closed-Book Exam
**This is a CLOSED-BOOK exam. The question must be completely self-contained.**

- The **knowledge tested** MUST come from the Course Material
- But the **question text** must NOT reference external materials
- Include ALL necessary information (code, data, context) directly in the question

**DO NOT write**:
- "According to the lecture material..."
- "As shown in the slides..."
- "Referring to the course notes..."

**INSTEAD write**:
- "Given the following code: [code], what is the output?"
- "Consider a hash table that uses linear probing..."
- "A developer is debugging a program that..."

## Key Requirements
1. **Knowledge Source**: Extract a specific concept, rule, or technique from the Course Material below. The question MUST accurately test this knowledge.
2. **Be Creative**: 
   - Create a realistic scenario (e.g., "Alice is trying to...", "A developer wants to...").
   - Test practical understanding, not just memorization.
3. **Difficulty**: {f"Generate a **{target_difficulty.upper()}** difficulty question." if target_difficulty else "Undergraduate exam level (medium difficulty)."}
   - **easy**: Basic concept recall, straightforward application
   - **medium**: Requires understanding multiple concepts or common edge cases
   - **hard**: Complex scenarios, subtle distinctions, or advanced topics
4. **Four Options**: Provide exactly 4 plausible options (A, B, C, D). Include common misconceptions as distractors.
5. **Detailed Explanation**: Explain why the correct answer is right AND why each wrong option is incorrect.
6. **Citation (REQUIRED)**: Cite the exact section / passage of the Course Material below that justifies the answer.

## Output Format (JSON only)
{{
  "topic": "{matching_topic}",
  "difficulty": "easy" or "medium" or "hard",
  "question": "A scenario-based question text...",
  "options": ["A. Option", "B. Option", "C. Option", "D. Option"],
  "answer": "A. The full correct option text",
  "explanation": "Detailed explanation covering all options...",
  "source_chapter": "Section / sub-heading of the course material that the answer comes from",
  "source_excerpt": "A short verbatim quote from the Course Material (≤140 chars) that proves the answer."
}}

**IMPORTANT: Code Formatting**
If any option contains code (e.g., function definitions, shell commands, SQL queries), you MUST preserve code formatting with proper newlines (`\n`) and indentation. For example:
- WRONG: `"A. char* foo() {{ int x = 1; return x; }}"`
- CORRECT: `"A. char* foo() {{\n    int x = 1;\n    return x;\n}}"`
"""

    if seed_question:
        prompt += f"""
---
## Reference Question (for difficulty/style reference ONLY, do NOT copy):
{seed_question}
"""

    prompt += f"""
---
## Course Material ({matching_topic}) - USE THIS TO CREATE YOUR QUESTION:
{context_snippet}
"""

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert exam question designer. Output ONLY valid JSON. Be creative and divergent."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.9,  # Higher temperature for more creativity
            **non_thinking_kwargs(),
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        result["seed_question"] = seed_question if seed_question else f"Topic: {matching_topic}"
        result["course_id"] = course_id
        # Use target difficulty if specified
        if target_difficulty and target_difficulty in ["easy", "medium", "hard"]:
            result["difficulty"] = target_difficulty
        elif result.get("difficulty") not in ["easy", "medium", "hard"]:
            result["difficulty"] = "medium"
        return result
    except Exception as e:
        return {"error": str(e)}


def _pick_topic_and_context(topic, course_id, context_data):
    """Resolve topic name to a context_data key, return (topic_key, snippet)."""
    matching_topic = None
    for key in context_data.keys():
        if topic.lower() == key.lower():
            matching_topic = key
            break
    if not matching_topic:
        for key in context_data.keys():
            if key.lower().endswith('-' + topic.lower()):
                matching_topic = key
                break
    if not matching_topic:
        candidates = [k for k in context_data.keys() if topic.lower() in k.lower() or k.lower() in topic.lower()]
        if candidates:
            matching_topic = min(candidates, key=len)
    if not matching_topic and context_data:
        matching_topic = list(context_data.keys())[0]

    full_text = context_data.get(matching_topic, "")
    if len(full_text) > 50000:
        start_idx = random.randint(0, len(full_text) - 50000)
        snippet = full_text[start_idx : start_idx + 50000]
    else:
        snippet = full_text
    return matching_topic, snippet


def generate_fill_question(topic, course_id=None, context_data=None, target_difficulty=None, num_blanks=None):
    """Generate a fill-in-the-blank question for a specific topic.

    Returns dict with keys: question, answer (joined by '|||' if multi-blank),
    explanation, topic, difficulty, num_blanks.
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}

    if course_id is None:
        course_id = get_default_course()
    if context_data is None:
        context_data = parse_courseware(course_id)

    course_config = get_course(course_id)
    course_name = course_config.get("name", "Course") if course_config else "Course"

    matching_topic, snippet = _pick_topic_and_context(topic, course_id, context_data)
    if num_blanks is None:
        num_blanks = random.choice([1, 1, 2])  # mostly 1, sometimes 2

    prompt = f"""You are an expert university exam question designer for a "{course_name}" course.

## Your Goal
Create an **original FILL-IN-THE-BLANK question** for the topic "{matching_topic}".

## Format Rules
1. The question text MUST contain exactly {num_blanks} blank(s) marked as `____` (four underscores).
2. Each blank should test a precise term, concept, value, or short phrase from the Course Material.
3. Avoid trivially-guessable blanks; aim for terms a student must recall to answer.
4. Provide the correct answer(s) — for multiple blanks, separate them with `|||` in the same left-to-right order they appear.
5. Include a brief explanation that justifies the answer using the Course Material.

## CRITICAL: Self-Contained
This is a closed-book exam. The question must NOT reference "the lecture" / "the slides" / "the material".
Embed any required context (definitions, code, scenarios) directly in the question text.

## Difficulty: {f'Generate **{target_difficulty.upper()}** difficulty.' if target_difficulty else 'Choose easy/medium/hard yourself.'}
- easy: direct term recall
- medium: term used in a concrete scenario
- hard: subtle distinctions, combinations of concepts

## Output Format (JSON only)
{{
  "topic": "{matching_topic}",
  "difficulty": "easy" or "medium" or "hard",
  "question": "Question text with ____ blank(s)",
  "answer": "answer1{('|||answer2' if num_blanks > 1 else '')}",
  "explanation": "Why these answers are correct, citing the relevant concept.",
  "num_blanks": {num_blanks},
  "source_chapter": "Section / sub-heading of the course material the answer comes from",
  "source_excerpt": "A short verbatim quote from the Course Material (≤140 chars) that proves the answer."
}}

---
## Course Material ({matching_topic}):
{snippet}
"""

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert exam question designer. Output ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.85,
            **non_thinking_kwargs(),
        )
        result = json.loads(response.choices[0].message.content)
        result["course_id"] = course_id
        result["question_type"] = "fill"
        result["seed_question"] = f"Topic: {matching_topic} (fill)"
        if target_difficulty in ("easy", "medium", "hard"):
            result["difficulty"] = target_difficulty
        elif result.get("difficulty") not in ("easy", "medium", "hard"):
            result["difficulty"] = "medium"
        return result
    except Exception as e:
        return {"error": str(e)}


def generate_essay_question(topic, course_id=None, context_data=None, target_difficulty=None):
    """Generate an essay/discussion question with a model answer + grading rubric.

    Returns dict with: question, answer (model answer), explanation (rubric),
    topic, difficulty.
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}

    if course_id is None:
        course_id = get_default_course()
    if context_data is None:
        context_data = parse_courseware(course_id)

    course_config = get_course(course_id)
    course_name = course_config.get("name", "Course") if course_config else "Course"

    matching_topic, snippet = _pick_topic_and_context(topic, course_id, context_data)

    prompt = f"""You are an expert university exam question designer for a "{course_name}" course.

## Your Goal
Create an **original ESSAY / DISCUSSION question** for the topic "{matching_topic}" suitable for a final exam.

## Question Style
- Open-ended; expects 200–500 words of student response.
- Tests understanding, comparison, application, or critique — NOT just recall.
- Good prompts start with: "Discuss…", "Compare and contrast…", "Explain how…", "Analyze the role of…", "Evaluate the trade-offs of…", "Argue for or against…".
- Self-contained (no "as in the slides" references).

## Output Requirements
1. **answer**: A concise but complete model answer (~200–300 words) that earns full marks.
2. **explanation**: A grading rubric — list of 3–6 key points the student must mention to score well, formatted as a markdown list. Each point includes the weighting in parentheses, e.g. "- (3 marks) Defines the concept correctly."
3. The total marks across the rubric should sum to 10.

## Difficulty: {f'Generate **{target_difficulty.upper()}** difficulty.' if target_difficulty else 'Default to medium for exam-style essays.'}
- easy: definitions + a single example
- medium: comparison or application across 2–3 concepts
- hard: critique, trade-off analysis, multi-step reasoning

## Output Format (JSON only)
{{
  "topic": "{matching_topic}",
  "difficulty": "easy" or "medium" or "hard",
  "question": "The essay prompt (1–3 sentences).",
  "answer": "Model answer in paragraph form, ~200–300 words.",
  "explanation": "- (X marks) point 1\\n- (Y marks) point 2\\n- (Z marks) point 3 …",
  "source_chapter": "Primary chapter / sub-heading the prompt covers",
  "source_excerpt": "A short verbatim quote from the Course Material (≤140 chars) anchoring the topic."
}}

---
## Course Material ({matching_topic}):
{snippet}
"""

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert exam question designer. Output ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
            **non_thinking_kwargs(),
        )
        result = json.loads(response.choices[0].message.content)
        result["course_id"] = course_id
        result["question_type"] = "essay"
        result["seed_question"] = f"Topic: {matching_topic} (essay)"
        if target_difficulty in ("easy", "medium", "hard"):
            result["difficulty"] = target_difficulty
        elif result.get("difficulty") not in ("easy", "medium", "hard"):
            result["difficulty"] = "medium"
        return result
    except Exception as e:
        return {"error": str(e)}


def grade_essay_answer(question_text, model_answer, rubric, student_answer,
                       course_id=None, generation_context=None):
    """Grade a student's free-text essay answer against the rubric.

    If `generation_context` is supplied (saved at generation time), the grader
    treats its `chapter_excerpt` as ground truth so scoring stays reproducible
    even if the courseware on disk has since changed.

    Returns dict with: score, max_score, feedback (markdown), matched_points,
    missing_points, improvement_suggestions.
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}

    course_config = get_course(course_id) if course_id else None
    course_name = course_config.get("name", "Course") if course_config else "Course"

    gc = generation_context or {}
    max_score = gc.get("marks_total") or 10
    chapter_excerpt = gc.get("chapter_excerpt") or ""
    rubric_breakdown = gc.get("rubric_breakdown") or []
    is_original = gc.get("is_original")

    ground_truth_block = ""
    if chapter_excerpt:
        ground_truth_block = (
            "\n## Ground Truth (the chapter material the question was generated from)\n"
            f"{chapter_excerpt[:8000]}\n"
            "Use this passage as the authoritative reference. Award marks only for content "
            "supported by this passage (or universally-true equivalents).\n"
        )

    rubric_block = rubric or ""
    if rubric_breakdown:
        rubric_block = (
            rubric_block
            + "\n\n### Mark allocation (machine-readable)\n"
            + "\n".join(
                f"- ({r.get('marks','?')} marks) {r.get('criterion','')} — key points: "
                f"{'; '.join(r.get('key_points') or [])}"
                for r in rubric_breakdown
            )
        )

    origin_note = ""
    if is_original is True:
        origin_note = "\nThis is an EXAM-PAPER ORIGINAL — apply the paper's own rubric strictly.\n"

    prompt = f"""You are a fair, rigorous grader for a "{course_name}" course.{origin_note}

Grade the student's essay answer against the rubric below.

## Question
{question_text}

## Model Answer (for reference; this earns full marks)
{model_answer}

## Rubric (total {max_score} marks)
{rubric_block}
{ground_truth_block}
## Student Answer
{student_answer}

## Instructions
1. Read the student answer carefully.
2. For each rubric criterion, decide whether the student covered the listed key_points (fully / partially / not at all) and award proportional marks. Mark sub-totals MUST sum to ≤ marks_total.
3. Accept paraphrases and alternative valid arguments that are supported by the ground-truth passage if provided.
4. Do NOT award marks for irrelevant filler or for claims that contradict the ground truth.
5. Suggest 2–3 concrete improvements the student could make.

## Output Format (JSON only)
{{
  "score": <number 0-{max_score}, decimals OK>,
  "max_score": {max_score},
  "matched_points": ["short summary of each rubric point the student covered"],
  "missing_points": ["short summary of each rubric point the student missed or got wrong"],
  "improvement_suggestions": ["2–3 actionable, specific suggestions in Chinese"],
  "feedback": "2–4 sentence personalised feedback in Chinese — encouraging but honest, name 1 strength + 1 priority improvement."
}}
"""

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a rigorous but fair exam grader. Output ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2400,
            **non_thinking_kwargs(),
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}


def grade_fill_answer(correct_answer, student_answer):
    """Locally grade a fill-in-the-blank answer (no LLM call).

    Compares pipe-separated answers case-insensitively with whitespace stripped.
    Returns dict with: correct (bool), per_blank (list of bool), expected (list).
    """
    expected = [a.strip() for a in (correct_answer or '').split('|||')]
    given = [a.strip() for a in (student_answer or '').split('|||')]
    # Pad shorter list with empty strings
    while len(given) < len(expected):
        given.append('')
    per_blank = [g.lower() == e.lower() and e != '' for g, e in zip(given, expected)]
    return {
        "correct": all(per_blank) and len(per_blank) > 0,
        "per_blank": per_blank,
        "expected": expected,
    }


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


def batch_generate_typed(course_id, question_type, limit, target_difficulty=None, topic=None):
    """Batch-generate questions of a given type for a course.

    Distributes generation across all available topics (or focuses on one if `topic` set).
    """
    if course_id is None:
        course_id = get_default_course()
    context = parse_courseware(course_id)
    if not context:
        return []

    if topic:
        topics = [topic]
    else:
        topics = list(context.keys())

    results = []
    for i in range(limit):
        chosen_topic = topics[i % len(topics)]
        if question_type == "mcq":
            result = generate_question_for_topic(chosen_topic, course_id, context, target_difficulty)
        elif question_type == "fill":
            result = generate_fill_question(chosen_topic, course_id, context, target_difficulty)
        elif question_type == "essay":
            result = generate_essay_question(chosen_topic, course_id, context, target_difficulty)
        else:
            continue
        if "error" not in result:
            results.append(result)
    return results


# ────────── Knowledge points (study notes) ──────────────────────────────

def generate_knowledge_points(topic, course_id=None, context_data=None):
    """Extract structured study notes from a courseware chapter.

    The model decides how many points are needed to fully cover the chapter
    — no fixed N. Each point is small enough to memorise in isolation:
    one concept, one sentence definition, a few supporting bullets, and
    the source excerpt it was distilled from.

    Returns: {"points": [...], "topic": str} or {"error": str}
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}

    if course_id is None:
        course_id = get_default_course()
    if context_data is None:
        context_data = parse_courseware(course_id)

    course_config = get_course(course_id)
    course_name = course_config.get("name", "Course") if course_config else "Course"

    matching_topic, snippet = _pick_topic_and_context(topic, course_id, context_data)

    prompt = f"""You are a senior study-notes editor preparing exam-ready memorisation cards from lecture material.

## Course
{course_name}

## Chapter
{matching_topic}

## Your Task
Extract **EVERY distinct knowledge point** in the chapter below. Aim for **complete coverage with no omissions** — if a concept, definition, rule, list, framework, comparison, example, or pitfall appears in the material, it deserves a point. Quantity is determined by the chapter, not by a target count.

Each point must be:
1. **Atomic** — one concept, ready to memorise on its own.
2. **Self-contained** — readable without seeing other points.
3. **Anchored** — backed by a verbatim excerpt from the source.

## Each Point Carries
- `title`: the concept name (Chinese or English, follow the source).
- `definition`: ONE sentence that captures the concept precisely. This is the line the student would recite on an exam.
- `details`: 3–6 markdown-friendly bullets that expand the concept (mechanics, sub-points, examples, comparisons, pitfalls). Each bullet stays a single line.
- `importance`: `"core"` for concepts that exam questions are likely to ask, `"supporting"` for context / examples / nice-to-know.
- `source_excerpt`: a verbatim quote (≤200 chars) from the chapter that proves the point.
- `source_chapter`: the sub-section heading inside the chapter (e.g. `"L4 § Aggregation"`). Use the chapter heading itself if no sub-heading exists.

## Output Format (JSON only)
{{
  "topic": "{matching_topic}",
  "points": [
    {{
      "title": "...",
      "definition": "...",
      "details": ["...", "...", "..."],
      "importance": "core" | "supporting",
      "source_excerpt": "...",
      "source_chapter": "..."
    }}
    // ... as many as the chapter requires; do not invent points not in the source
  ]
}}

## CRITICAL
- Do NOT pad. Do NOT invent. If a point is not in the source, omit it.
- Do NOT collapse two distinct concepts into one point.
- Do NOT translate — keep the source language unless mixing aids clarity.
- Order points the way they appear in the chapter so reading them top-to-bottom feels like reading the chapter.

---
## Chapter Material
{snippet}
"""

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a meticulous study-notes editor. Output ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=8000,
            **non_thinking_kwargs(),
        )
        result = json.loads(response.choices[0].message.content)
        result["course_id"] = course_id
        return result
    except Exception as e:
        return {"error": str(e)}


def generate_essays_for_chapter_from_paper(
    course_id: str,
    chapter_topic: str,
    paper_text: str,
    *,
    context_data=None,
    num_samples: int = 2,
):
    """Per-chapter essay batch grounded in a real mock exam paper.

    The model receives the WHOLE mock paper (so it learns the exam's style,
    rigour and mark structure) plus the courseware for ONE chapter. It then
    returns two lists:

      * `originals` — questions lifted verbatim from the paper that this
        chapter could legitimately host (zero, one or more depending on the
        paper). Each original keeps the paper's own sample-answer rubric.
      * `samples` — `num_samples` fresh exam-style variants that test
        different aspects of the same chapter (no overlap with the
        originals' subject matter).

    Every produced question is attached with the full generation context so
    the grader can later score against the same evidence the LLM saw —
    independent of any future courseware edits.
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}

    if context_data is None:
        context_data = parse_courseware(course_id)

    course_config = get_course(course_id)
    course_name = course_config.get("name", "Course") if course_config else "Course"

    matching_topic, snippet = _pick_topic_and_context(chapter_topic, course_id, context_data)

    prompt = f"""You are an expert university exam question designer for a "{course_name}" course.

Below you have:
1. **The full text of a real mock final exam paper** (questions + official sample answers).
2. **Course material for ONE chapter**: `{matching_topic}`.

Your job, for THIS chapter only:

A. **Originals** — Look at every question and sub-question in the mock paper. Identify the ones whose subject matter clearly belongs to THIS chapter's material. Lift them verbatim. Convert the paper's "Sample answer" into a structured rubric (criterion + marks + key points). Preserve the original mark allocation.

B. **Samples** — Generate exactly `{num_samples}` fresh exam-style essay questions that:
   - Cover aspects of THIS chapter that are NOT addressed by the originals you extracted.
   - Match the paper's tone, rigour and mark distribution.
   - Use a concrete fictional scenario where appropriate (different from any used in the originals).
   - Total marks per sample should be in the same range as the originals (e.g. 5–25 marks).

For every produced question (originals AND samples) you MUST include:
- `question`: the prompt text (verbatim for originals, original wording for samples)
- `answer`: the model answer (200–400 words for big questions; shorter for sub-parts)
- `rubric_breakdown`: array of `{{criterion, marks, key_points: [..]}}` summing to `marks_total`
- `marks_total`: integer total marks
- `source_chapter`: section/sub-heading inside the chapter material
- `source_excerpt`: a short verbatim quote (≤200 chars) from the chapter material proving the answer
- `is_original`: true for lifted-from-paper, false for new samples

If the chapter does not match any question in the paper, output an empty `originals` list and still produce `{num_samples}` samples.

## Output Format (JSON only)
{{
  "topic": "{matching_topic}",
  "originals": [ /* extracted from paper */ ],
  "samples":   [ /* {num_samples} fresh variants */ ]
}}

# ---- MOCK PAPER (style + difficulty reference) ----
{paper_text}

# ---- CHAPTER MATERIAL ({matching_topic}) ----
{snippet}
"""

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are a meticulous senior exam question designer. Output ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.45,
            max_tokens=12000,
            **non_thinking_kwargs(),
        )
        result = json.loads(response.choices[0].message.content)
        result["course_id"] = course_id
        result["chapter_topic"] = matching_topic
        # Attach the chapter excerpt so callers can ship it into generation_context
        result["_chapter_excerpt"] = snippet
        return result
    except Exception as e:
        return {"error": str(e)}


def add_citation_to_question(question, course_id=None, context_data=None):
    """Generate `source_chapter` + `source_excerpt` for an existing question.

    Used by `manage.py backfill_citations` to retrofit the citation fields
    onto questions generated before the citation prompt landed.

    Returns: {"source_chapter": str, "source_excerpt": str} or {"error": str}
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}

    if course_id is None:
        course_id = question.course_id
    if context_data is None:
        context_data = parse_courseware(course_id)

    matching_topic, snippet = _pick_topic_and_context(question.topic, course_id, context_data)

    options_block = ""
    if question.question_type == "mcq" and isinstance(question.options, list):
        options_block = "\n## Options\n" + "\n".join(question.options)

    prompt = f"""Locate the exact passage in the course material below that justifies the answer to this question.

## Topic
{matching_topic}

## Question
{question.question_text}
{options_block}

## Stated Answer
{question.answer}

## Your Task
Return JSON with two fields:
- `source_chapter`: the sub-section heading the answer is grounded in (e.g. "L4 § Aggregation").
- `source_excerpt`: a short verbatim quote (≤140 chars) from the material below that proves the answer.

If the chapter material truly does not contain support for the answer, return:
{{"source_chapter": "", "source_excerpt": ""}}

## Output (JSON only)
{{
  "source_chapter": "...",
  "source_excerpt": "..."
}}

---
## Course Material ({matching_topic})
{snippet}
"""

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You are a meticulous citation editor. Output ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=400,
            **non_thinking_kwargs(),
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}
