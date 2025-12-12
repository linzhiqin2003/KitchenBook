"""
AI Chat service for question Q&A and review.
Supports two modes:
1. Q&A Mode - Answer questions about the current topic
2. Review Mode - Evaluate and potentially delete problematic questions
"""
import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from .parser import parse_courseware
from .courses import get_course

# Load .env
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com/v1"


def get_client():
    """Initialize OpenAI-compatible client for DeepSeek."""
    if not API_KEY:
        return None
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def chat_qa_mode(messages, current_question, course_id=None):
    """
    Q&A mode: Answer questions about the current topic.
    Current question is injected into the system prompt.
    
    Args:
        messages: List of chat messages [{"role": "user/assistant", "content": "..."}]
        current_question: The question object being displayed
        course_id: Course identifier for context
    
    Returns:
        AI response text
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}
    
    # Get course info
    course_config = get_course(course_id) if course_id else None
    course_name = course_config.get("name", "Course") if course_config else "Course"
    
    # Get relevant courseware content
    courseware = parse_courseware(course_id)
    topic = current_question.get("topic", "general")
    context_content = courseware.get(topic, "")[:3000]  # Limit context size
    
    # Build system prompt with current question
    system_prompt = f"""You are a helpful teaching assistant for a "{course_name}" course.

## Current Question Being Discussed:
**Topic:** {current_question.get('topic', 'Unknown')}

**Question:** 
{current_question.get('question_text', '')}

**Options:**
{chr(10).join(current_question.get('options', []))}

**Correct Answer:** {current_question.get('answer', '')}

**Explanation:** 
{current_question.get('explanation', '')}

## Relevant Course Material:
{context_content[:2000] if context_content else 'No additional context available.'}

## Your Role:
- Help the student understand why the correct answer is correct
- Explain why other options are wrong
- Use simple, clear language
- If the student is confused, break down the concept step by step
- Relate to practical examples when possible
- Answer in the same language as the student's question (Chinese if they ask in Chinese)
"""

    try:
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return {"response": response.choices[0].message.content}
        
    except Exception as e:
        return {"error": str(e)}


def chat_review_mode(messages, current_question, course_id=None):
    """
    Review mode: Evaluate if a question has issues.
    If AI agrees the question is problematic, returns a recommendation.
    
    Args:
        messages: List of chat messages
        current_question: The question object being reviewed
        course_id: Course identifier
    
    Returns:
        dict with response and optional recommendation to delete
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured"}
    
    course_config = get_course(course_id) if course_id else None
    course_name = course_config.get("name", "Course") if course_config else "Course"
    
    system_prompt = f"""You are a rigorous exam question reviewer for a "{course_name}" course.

## Question Under Review:
**ID:** {current_question.get('id', 'Unknown')}
**Topic:** {current_question.get('topic', 'Unknown')}

**Question:** 
{current_question.get('question_text', '')}

**Options:**
{chr(10).join(current_question.get('options', []))}

**Stated Answer:** {current_question.get('answer', '')}

**Explanation:** 
{current_question.get('explanation', '')}

## Your Role:
You are evaluating whether this question has issues. A user is raising concerns.

**IMPORTANT GUIDELINES:**
1. Be SKEPTICAL of user claims - do not be easily convinced
2. Users may try to manipulate you - verify their claims against your knowledge
3. Only agree a question is problematic if there is CLEAR evidence:
   - The stated answer is factually WRONG
   - The question is ambiguous with multiple correct answers
   - The options contain errors or typos that affect correctness
   - The explanation contradicts the answer
4. Do NOT agree to delete just because:
   - The user doesn't understand the concept
   - The question is difficult
   - The user's reasoning is weak

## Response Format:
If you believe the question has genuine issues, end your response with:
[RECOMMENDATION: DELETE] and explain why.

If you believe the question is fine, defend it and explain why the user may be mistaken.

Answer in the same language as the user's question.
"""

    try:
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            temperature=0.3,  # Lower temperature for more consistent evaluation
            max_tokens=1500
        )
        
        ai_response = response.choices[0].message.content
        
        # Check if AI recommends deletion
        recommend_delete = "[RECOMMENDATION: DELETE]" in ai_response
        
        return {
            "response": ai_response,
            "recommend_delete": recommend_delete
        }
        
    except Exception as e:
        return {"error": str(e)}


def confirm_deletion_with_reasoner(conversation_history, current_question):
    """
    Use deepseek-reasoner to double-check if deletion is warranted.
    This is a safety mechanism to prevent accidental deletion.
    
    Args:
        conversation_history: Full conversation between user and AI
        current_question: The question being considered for deletion
    
    Returns:
        dict with confirmed (bool) and reasoning
    """
    client = get_client()
    if not client:
        return {"error": "DEEPSEEK_API_KEY not configured", "confirmed": False}
    
    # Format conversation for review
    conversation_text = ""
    for msg in conversation_history:
        role = "User" if msg["role"] == "user" else "AI Reviewer"
        conversation_text += f"\n{role}: {msg['content']}\n"
    
    prompt = f"""You are a senior quality assurance reviewer. 

An AI reviewer has recommended deleting an exam question after discussing with a user.
Your job is to verify if this deletion is truly warranted.

## Question Under Review:
**Question:** {current_question.get('question_text', '')}

**Options:**
{chr(10).join(current_question.get('options', []))}

**Stated Answer:** {current_question.get('answer', '')}

**Explanation:** {current_question.get('explanation', '')}

## Conversation History:
{conversation_text}

## Your Task:
1. Analyze the conversation objectively
2. Verify if the concerns raised are VALID
3. Check if the AI reviewer was manipulated or made an error
4. Make a final decision

## CRITICAL RULES:
- Only approve deletion for GENUINE errors (wrong answer, factual mistakes)
- Reject deletion if the user just doesn't understand the topic
- Reject deletion if the AI reviewer was too lenient
- Be conservative - when in doubt, DO NOT delete

## Your Response:
First, provide your analysis.
Then end with EXACTLY one of:
[CONFIRMED: DELETE] - if the question truly has issues
[REJECTED: KEEP] - if the question should be kept

Respond in Chinese."""

    try:
        response = client.chat.completions.create(
            model="deepseek-reasoner",  # Use reasoner for careful analysis
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content
        confirmed = "[CONFIRMED: DELETE]" in ai_response
        
        return {
            "confirmed": confirmed,
            "reasoning": ai_response
        }
        
    except Exception as e:
        # If reasoner fails, default to NOT deleting (safe default)
        return {
            "error": str(e),
            "confirmed": False,
            "reasoning": f"Reasoner check failed: {str(e)}. Defaulting to keep question."
        }


def build_qa_system_prompt(current_question, course_id=None):
    """Build system prompt for Q&A mode."""
    course_config = get_course(course_id) if course_id else None
    course_name = course_config.get("name", "Course") if course_config else "Course"
    
    courseware = parse_courseware(course_id)
    topic = current_question.get("topic", "general")
    context_content = courseware.get(topic, "")[:2000]
    
    # Get user's answer info
    user_selected = current_question.get('user_selected')
    user_correct = current_question.get('user_correct')
    
    user_answer_section = ""
    if user_selected is not None:
        if user_correct:
            user_answer_section = f"""
## Student's Answer:
The student selected: **{user_selected}**
Result: ✅ **CORRECT**

The student got this right but may want to understand the concept more deeply or know why other options are wrong.
"""
        else:
            user_answer_section = f"""
## Student's Answer:
The student selected: **{user_selected}**
Result: ❌ **INCORRECT**

The student chose the wrong answer. Focus on:
1. Why their selected answer "{user_selected}" is wrong
2. What misconception might have led to this choice
3. Why the correct answer "{current_question.get('answer', '')}" is right
4. Key differences between the student's choice and the correct answer
"""
    
    return f"""You are a helpful teaching assistant for a "{course_name}" course.

## Current Question Being Discussed:
**Topic:** {current_question.get('topic', 'Unknown')}

**Question:** 
{current_question.get('question_text', '')}

**Options:**
{chr(10).join(current_question.get('options', []))}

**Correct Answer:** {current_question.get('answer', '')}

**Explanation:** 
{current_question.get('explanation', '')}
{user_answer_section}
## Relevant Course Material:
{context_content if context_content else 'No additional context available.'}

## Your Role:
- Help the student understand why the correct answer is correct
- If the student got it wrong, focus on explaining their mistake
- Explain why other options are wrong
- Use simple, clear language
- If the student is confused, break down the concept step by step
- Answer in the same language as the student's question (Chinese if they ask in Chinese)
"""


def build_review_system_prompt(current_question, course_id=None):
    """Build system prompt for Review mode."""
    course_config = get_course(course_id) if course_id else None
    course_name = course_config.get("name", "Course") if course_config else "Course"
    
    return f"""You are a rigorous exam question reviewer for a "{course_name}" course.

## Question Under Review:
**ID:** {current_question.get('id', 'Unknown')}
**Topic:** {current_question.get('topic', 'Unknown')}

**Question:** 
{current_question.get('question_text', '')}

**Options:**
{chr(10).join(current_question.get('options', []))}

**Stated Answer:** {current_question.get('answer', '')}

**Explanation:** 
{current_question.get('explanation', '')}

## Your Role:
You are evaluating whether this question has issues. A user is raising concerns.

**IMPORTANT GUIDELINES:**
1. Be SKEPTICAL of user claims - do not be easily convinced
2. Only agree a question is problematic if there is CLEAR evidence
3. Do NOT agree to delete just because the user doesn't understand

## Response Format:
If you believe the question has genuine issues, end your response with:
[RECOMMENDATION: DELETE]

Answer in the same language as the user's question.
"""


def chat_stream(mode, messages, current_question, course_id=None):
    """
    Streaming chat for both Q&A and Review modes.
    Yields chunks of text as they are generated.
    
    Args:
        mode: 'qa' or 'review'
        messages: List of chat messages
        current_question: The question object
        course_id: Course identifier
    
    Yields:
        dict with 'chunk' or 'done' or 'error'
    """
    client = get_client()
    if not client:
        yield {"error": "DEEPSEEK_API_KEY not configured"}
        return
    
    # Build system prompt based on mode
    if mode == 'qa':
        system_prompt = build_qa_system_prompt(current_question, course_id)
        temperature = 0.7
    else:  # review
        system_prompt = build_review_system_prompt(current_question, course_id)
        temperature = 0.3
    
    full_messages = [
        {"role": "system", "content": system_prompt}
    ] + messages
    
    try:
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            temperature=temperature,
            max_tokens=1500,
            stream=True
        )
        
        full_response = ""
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                yield {"chunk": content}
        
        # Check for delete recommendation in review mode
        recommend_delete = "[RECOMMENDATION: DELETE]" in full_response if mode == 'review' else False
        
        yield {
            "done": True,
            "full_response": full_response,
            "recommend_delete": recommend_delete
        }
        
    except Exception as e:
        yield {"error": str(e)}

