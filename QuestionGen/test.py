import os
import re
import json
import glob
from dotenv import load_dotenv
from openai import OpenAI

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

# parse_simulation_questions("software-tools/tb1-example_ocr.md")

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

# print(parse_courseware("software-tools"))
parse_courseware("software-tools")