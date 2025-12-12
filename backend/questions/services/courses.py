"""
Standardized Course Configuration System.

Each course follows the same structure:
courses/
└── {course-id}/
    ├── courseware/       # Markdown courseware files (can have subdirs)
    ├── simulation/       # OCR-ed simulation/mock exam files
    └── config.json       # Course metadata and topic keywords

config.json format:
{
    "name": "Course Name",
    "display_name": "Display Name for UI",
    "description": "Course description",
    "icon": "🎯",
    "topic_keywords": {
        "topic-name": ["keyword1", "keyword2", ...]
    }
}
"""
import os
import json
from pathlib import Path

# Base directory for all courses (repo root /courses)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
COURSES_DIR = PROJECT_ROOT / "courses"


def get_course_dir(course_id):
    """Get the directory path for a course."""
    return COURSES_DIR / course_id


def load_course_config(course_id):
    """
    Load course configuration from config.json.
    Returns None if course doesn't exist.
    """
    course_dir = get_course_dir(course_id)
    config_file = course_dir / "config.json"
    
    if not config_file.exists():
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Add computed paths
        config['id'] = course_id
        config['dir'] = course_dir
        config['courseware_dir'] = course_dir / "courseware"
        config['simulation_dir'] = course_dir / "simulation"
        config['exists'] = True
        
        return config
    except (json.JSONDecodeError, IOError):
        return None


def get_all_courses():
    """
    Discover and load all available courses.
    Scans the courses directory for valid course folders.
    """
    if not COURSES_DIR.exists():
        return {}
    
    courses = {}
    for item in sorted(COURSES_DIR.iterdir(), key=lambda p: p.name):
        if item.is_dir() and not item.name.startswith('.'):
            config = load_course_config(item.name)
            if config:
                courses[item.name] = {
                    "id": item.name,
                    "name": config.get("name", item.name),
                    "display_name": config.get("display_name", config.get("name", item.name)),
                    "description": config.get("description", ""),
                    "icon": config.get("icon", "📚"),
                    "exists": True
                }
    
    return courses


def get_course(course_id):
    """Get full course configuration by ID."""
    return load_course_config(course_id)


def get_available_courses():
    """Alias for get_all_courses (all discovered courses are available)."""
    return get_all_courses()


def get_default_course():
    """Get the default course (prefer legacy 'software-tools' when present)."""
    courses = get_all_courses()
    if not courses:
        return None
    if "software-tools" in courses:
        return "software-tools"
    return next(iter(courses))


def get_courseware_path(course_id):
    """Get the courseware directory path for a course."""
    return get_course_dir(course_id) / "courseware"


def get_simulation_path(course_id):
    """Get the simulation directory path for a course."""
    return get_course_dir(course_id) / "simulation"


def get_topic_keywords(course_id):
    """Get topic keywords mapping for a course."""
    config = load_course_config(course_id)
    if config:
        return config.get("topic_keywords", {})
    return {}


def create_course_template(course_id, name, description="", icon="📚"):
    """
    Create a new course with the standard directory structure.
    Returns True if successful, False if course already exists.
    """
    course_dir = get_course_dir(course_id)
    
    if course_dir.exists():
        return False
    
    # Create directories
    os.makedirs(course_dir / "courseware", exist_ok=True)
    os.makedirs(course_dir / "simulation", exist_ok=True)
    
    # Create config.json
    config = {
        "name": name,
        "display_name": f"{name} 刷题",
        "description": description,
        "icon": icon,
        "topic_keywords": {}
    }
    
    with open(course_dir / "config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    # Create README
    readme_content = f"""# {name}

## 目录结构

- `courseware/` - 放置课件Markdown文件
  - 可以使用子目录组织不同主题
  - 例如: `01-basics/`, `02-advanced/`
  
- `simulation/` - 放置模拟题OCR后的Markdown文件
  - 文件名格式: `exam-name_ocr.md`
  
- `config.json` - 课程配置

## 配置说明

编辑 `config.json` 添加主题关键词:

```json
{{
  "topic_keywords": {{
    "topic-name": ["keyword1", "keyword2"]
  }}
}}
```
"""
    
    with open(course_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    return True
