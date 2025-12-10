import os
import re
import json
import glob
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com"  # Verify specific DeepSeek API endpoint
COURSEWARE_DIR = "software-tools"
SIMULATION_FILE = "software-tools/tb1-example_ocr.md"
OUTPUT_FILE = "question_bank.json"

def get_client():
    if not API_KEY:
        print("Warning: DEEPSEEK_API_KEY not found in environment variables.")
        return None
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)

def parse_simulation_questions(file_path):
    """
    Parses the OCR markdown file to extract questions.
    Assumes format: Q<number>. <Text> ... A. <Option> ...
    """
    print(f"Parsing simulation questions from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find questions blocks.
    # Looking for Q[number]. followed by text, until the next Q[number]. or end.
    # This is a simple parser and might need refinement based on exact OCR quirks.
    question_pattern = re.compile(r'(Q\d+\..*?)(?=Q\d+\.|$)', re.DOTALL)
    
    matches = question_pattern.findall(content)
    questions = []
    
    for match in matches:
        # Clean up the text
        clean_text = match.strip()
        # Basic extraction of lines to determine if it's a valid question block
        if "A." in clean_text and "B." in clean_text:
            questions.append(clean_text)
            
    print(f"Found {len(questions)} simulation questions.")
    return questions

def parse_courseware(root_dir):
    """
    Reads markdown files from the courseware directory and groups them by topic.
    Top-level directories (e.g., 01-sysadmin) are treated as topics.
    """
    print(f"Parsing courseware from {root_dir}...")
    context_by_topic = {}
    
    # Get immediate subdirectories
    try:
        subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    except FileNotFoundError:
        print(f"Directory {root_dir} not found.")
        return {}

    for subdir in subdirs:
        # Topic name from directory (e.g., "01-sysadmin" -> "sysadmin")
        topic_match = re.search(r'\d+-(.*)', subdir)
        topic = topic_match.group(1) if topic_match else subdir
        
        topic_path = os.path.join(root_dir, subdir)
        topic_content = []
        
        # Read all .md files recursively in this topic
        md_files = glob.glob(os.path.join(topic_path, "**/*.md"), recursive=True)
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    topic_content.append(f.read())
            except Exception as e:
                print(f"Error reading {md_file}: {e}")
        
        if topic_content:
            context_by_topic[topic] = "\n\n".join(topic_content)
            
    print(f"Loaded context for topics: {list(context_by_topic.keys())}")
    return context_by_topic

def infer_topic(question_text, topics):
    """
    Simple keyword matching to guess the topic of a seed question.
    """
    question_lower = question_text.lower()
    scores = {topic: 0 for topic in topics}
    
    for topic in topics:
        # Normalize topic name for matching (e.g., 'sysadmin', 'git')
        if topic in question_lower:
            scores[topic] += 5
        # Add more specific keywords here if needed
        
    # Return the topic with max score, or a default/random if all zero
    best_topic = max(scores, key=scores.get)
    return best_topic if scores[best_topic] > 0 else "general"

def generate_question(client, seed_question, context_data):
    """
    Uses the API to generate a new question based on the seed and context.
    """
    topics = list(context_data.keys())
    topic = infer_topic(seed_question, topics)
    
    context_snippet = ""
    if topic in context_data:
        # Limit context size to avoid token limits (aggressive truncation for now)
        # Taking the first 2000 characters of the topic content as a sample
        context_snippet = context_data[topic][:3000] 
    else:
        # Fallback context
        context_snippet = "General Software Tools knowledge."

    prompt = f"""
You are an expert exam question generator for a Software Tools course.
I will provide you with a "Seed Question" from a past exam and some "Course Context" related to the likely topic.

Your task:
1. Analyze the Seed Question to understand its difficulty, style (multiple choice), and specific technical concept.
2. Generate a *new* multiple-choice question that tests a similar concept or a related concept from the provided Context.
3. The new question should be distinct from the seed but similar in complexity.
4. Provide 4 options (A, B, C, D).
5. detailed explanation of why the correct answer is correct and why others are wrong.

Output format: JSON ONLY.
{{
  "topic": "{topic}",
  "question": "The question text...",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "answer": "The text of the correct option",
  "explanation": "Detailed explanation..."
}}

Seed Question:
{seed_question}

Course Context ({topic}):
{context_snippet}
...
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # Check specific model name for DeepSeek
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error generating question: {e}")
        return None

def main():
    print("Starting Question Generator...")
    client = get_client()
    
    questions = parse_simulation_questions(SIMULATION_FILE)
    context = parse_courseware(COURSEWARE_DIR)
    
    generated_bank = []
    
    # For testing, just generate 3 questions
    print("Generating questions (limit 3 for testing)...")
    for i, seed in enumerate(questions[:3]):
        print(f"Generating question {i+1}...")
        if client:
            new_q = generate_question(client, seed, context)
            if new_q:
                generated_bank.append(new_q)
        else:
            print("Skipping API call (No Key).")
            # Mock data for testing flow
            generated_bank.append({
                "topic": "mock",
                "question": "Mock Question based on seed?",
                "options": ["A", "B", "C", "D"],
                "answer": "A",
                "explanation": "Mock explanation."
            })
            
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(generated_bank, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(generated_bank)} questions to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
