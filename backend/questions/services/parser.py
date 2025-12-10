"""
Markdown parser for courseware and simulation questions.
"""
import os
import re
import glob
from pathlib import Path

# Base directory for courseware (relative to backend directory)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
COURSEWARE_DIR = BACKEND_DIR / "questiongen-data"
SIMULATION_FILE = COURSEWARE_DIR / "tb1-example_ocr.md"


def parse_simulation_questions(file_path=None):
    """
    Extract questions from the OCR markdown file.
    Returns list of question text blocks.
    """
    file_path = file_path or SIMULATION_FILE
    
    if not os.path.exists(file_path):
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to capture Q{number}. blocks
    question_pattern = re.compile(r'(Q\d+\..*?)(?=Q\d+\.|\#\# 第\d+页|$)', re.DOTALL)
    matches = question_pattern.findall(content)
    
    questions = []
    for match in matches:
        clean_text = match.strip()
        # Validate it looks like a multiple-choice question
        if "A." in clean_text and "B." in clean_text:
            questions.append(clean_text)
    
    return questions


def parse_courseware(root_dir=None):
    """
    Read all markdown files from courseware directory.
    Returns dict: {topic_name: concatenated_content}
    """
    root_dir = root_dir or COURSEWARE_DIR
    
    if not os.path.exists(root_dir):
        return {}
    
    context_by_topic = {}
    
    try:
        subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    except FileNotFoundError:
        return {}

    for subdir in subdirs:
        # Extract topic name: "01-sysadmin" -> "sysadmin"
        topic_match = re.search(r'\d+-(.*)', subdir)
        topic = topic_match.group(1) if topic_match else subdir
        
        topic_path = os.path.join(root_dir, subdir)
        topic_content = []
        
        md_files = glob.glob(os.path.join(topic_path, "**/*.md"), recursive=True)
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    topic_content.append(f.read())
            except Exception:
                pass
        
        if topic_content:
            context_by_topic[topic] = "\n\n---\n\n".join(topic_content)
    
    return context_by_topic


def parse_courseware_with_sources(root_dir=None):
    """
    Read all markdown files from courseware directory with source tracking.
    Returns dict: {topic_name: {"content": str, "sources": [{"file": str, "content": str}]}}
    """
    root_dir = root_dir or COURSEWARE_DIR
    
    if not os.path.exists(root_dir):
        return {}
    
    context_by_topic = {}
    
    try:
        subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    except FileNotFoundError:
        return {}

    for subdir in subdirs:
        # Extract topic name: "01-sysadmin" -> "sysadmin"
        topic_match = re.search(r'\d+-(.*)', subdir)
        topic = topic_match.group(1) if topic_match else subdir
        
        topic_path = os.path.join(root_dir, subdir)
        sources = []
        combined_content = []
        
        md_files = glob.glob(os.path.join(topic_path, "**/*.md"), recursive=True)
        md_files.sort()  # Ensure consistent ordering
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    
                # Get relative path for display
                rel_path = os.path.relpath(md_file, root_dir)
                file_name = os.path.basename(md_file)
                
                # Add source marker to content
                marked_content = f"\n\n=== SOURCE: {rel_path} ===\n\n{file_content}"
                combined_content.append(marked_content)
                
                sources.append({
                    "file": rel_path,
                    "filename": file_name,
                    "content": file_content
                })
            except Exception:
                pass
        
        if sources:
            context_by_topic[topic] = {
                "content": "\n".join(combined_content),
                "sources": sources,
                "source_list": ", ".join([s["file"] for s in sources])
            }
    
    return context_by_topic


def infer_topic(question_text, topics):
    """
    Simple keyword matching to guess the topic of a question.
    """
    question_lower = question_text.lower()
    
    topic_keywords = {
        'sysadmin': ['ssh', 'apt', 'debian', 'server', 'vagrant', 'scp'],
        'fundamentals': ['pipe', 'shell', 'echo', 'permission', 'chmod', 'script'],
        'regex': ['grep', 'sed', 'regex', 'pattern', 'match'],
        'git': ['git', 'branch', 'commit', 'merge', 'pull', 'push', 'fetch'],
        'buildtools': ['make', 'maven', 'gcc', 'clang', 'compile', 'build'],
        'debugging': ['gdb', 'debug', 'segfault', 'strace', 'core dump'],
        'sql': ['sql', 'database', 'select', 'join', 'table', 'query']
    }
    
    scores = {t: 0 for t in topics}
    
    for topic in topics:
        # Direct match
        if topic in question_lower:
            scores[topic] += 3
        # Keyword match
        if topic in topic_keywords:
            for kw in topic_keywords[topic]:
                if kw in question_lower:
                    scores[topic] += 2
    
    best_topic = max(scores, key=scores.get) if scores else 'general'
    return best_topic if scores.get(best_topic, 0) > 0 else list(topics)[0] if topics else 'general'

