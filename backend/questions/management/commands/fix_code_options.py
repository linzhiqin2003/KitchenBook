"""
Django management command to fix code formatting in question options.

This script finds all questions with code-like options (e.g., C functions, SQL queries)
and uses AI to reformat them with proper newlines and indentation.

Usage:
    python manage.py fix_code_options         # Dry run - show what would be fixed
    python manage.py fix_code_options --apply # Actually apply the fixes
    python manage.py fix_code_options --limit 10 --apply  # Fix only 10 questions
"""
import json
import re
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from questions.models import Question
from openai import OpenAI
from dotenv import load_dotenv

# Load .env
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = "https://api.deepseek.com/v1"


def is_code_option(text):
    """Detect if an option contains code-like content."""
    if not text:
        return False
    # Check for code patterns
    code_patterns = [
        r'[{};]',                          # Braces and semicolons
        r'\b(int|void|char|return|if|for|while|class|def|SELECT|INSERT|UPDATE|DELETE)\b',
        r'\b(malloc|free|strcpy|strlen|printf|scanf)\b',  # C functions
        r'\(\s*\w+\s*\*\s*\)',             # Pointer declarations
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in code_patterns)


def needs_formatting(text):
    """Check if code option is missing newlines (all on one line)."""
    if not text:
        return False
    # If it looks like code but has no newlines and is long, it needs formatting
    has_code = is_code_option(text)
    has_no_newlines = '\n' not in text
    is_long = len(text) > 30
    return has_code and has_no_newlines and is_long


def format_code_option(client, option_text):
    """Use AI to reformat a single-line code option with proper newlines."""
    prompt = f"""Reformat the following code to have proper line breaks and indentation.
Keep the same logic and content, just add appropriate newlines and indentation.
Output ONLY the reformatted code, no explanations.

Original (single line):
{option_text}

Reformatted code:"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a code formatter. Output ONLY the reformatted code, nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for consistent formatting
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  Error formatting: {e}")
        return None


class Command(BaseCommand):
    help = 'Fix code formatting in question options by adding proper newlines'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually apply the fixes (default is dry run)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of questions to process',
        )
        parser.add_argument(
            '--course',
            type=str,
            default=None,
            help='Filter by course_id',
        )

    def handle(self, *args, **options):
        apply_fixes = options['apply']
        limit = options['limit']
        course_filter = options['course']

        if not API_KEY:
            self.stderr.write(self.style.ERROR('DEEPSEEK_API_KEY not configured in .env'))
            return

        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

        # Find questions with code options
        queryset = Question.objects.all()
        if course_filter:
            queryset = queryset.filter(course_id=course_filter)

        questions_to_fix = []
        
        self.stdout.write(f"Scanning {queryset.count()} questions...")
        
        for q in queryset:
            options_need_fix = []
            for i, opt in enumerate(q.options):
                if needs_formatting(opt):
                    options_need_fix.append(i)
            
            if options_need_fix:
                questions_to_fix.append((q, options_need_fix))

        self.stdout.write(self.style.WARNING(
            f"Found {len(questions_to_fix)} questions with code options needing formatting"
        ))

        if limit:
            questions_to_fix = questions_to_fix[:limit]
            self.stdout.write(f"Processing first {limit} questions only")

        if not apply_fixes:
            self.stdout.write(self.style.NOTICE("DRY RUN - No changes will be made. Use --apply to save changes."))
        
        fixed_count = 0
        error_count = 0

        for q, option_indices in questions_to_fix:
            self.stdout.write(f"\n--- Question ID: {q.id} (Topic: {q.topic}) ---")
            
            new_options = list(q.options)  # Make a copy
            question_fixed = False
            
            for idx in option_indices:
                old_option = q.options[idx]
                self.stdout.write(f"  Option {chr(65+idx)} (before):")
                self.stdout.write(f"    {old_option[:100]}...")
                
                # Format with AI
                formatted = format_code_option(client, old_option)
                
                if formatted and formatted != old_option:
                    # Preserve the A./B./C./D. prefix if present
                    prefix_match = re.match(r'^([A-D]\.?\s*)', old_option)
                    if prefix_match:
                        prefix = prefix_match.group(1)
                        # Remove prefix from formatted if AI included it
                        formatted = re.sub(r'^[A-D]\.?\s*', '', formatted)
                        formatted = prefix + formatted
                    
                    new_options[idx] = formatted
                    question_fixed = True
                    
                    self.stdout.write(self.style.SUCCESS(f"  Option {chr(65+idx)} (after):"))
                    # Show first few lines
                    for line in formatted.split('\n')[:5]:
                        self.stdout.write(f"    {line}")
                    if formatted.count('\n') > 4:
                        self.stdout.write(f"    ... ({formatted.count(chr(10))+1} lines total)")
                else:
                    self.stdout.write(self.style.WARNING(f"  Option {chr(65+idx)}: Could not format"))
                    error_count += 1
            
            if question_fixed and apply_fixes:
                q.options = new_options
                # Also fix answer if it matches an option
                for i, opt in enumerate(new_options):
                    if q.answer and (q.answer == q.options[i] or q.answer.startswith(chr(65+i) + '.')):
                        # Update answer to match reformatted option
                        old_prefix = re.match(r'^([A-D]\.?\s*)', q.answer)
                        if old_prefix:
                            q.answer = opt  # Use the new formatted option as answer
                q.save()
                self.stdout.write(self.style.SUCCESS(f"  ✓ Saved question {q.id}"))
                fixed_count += 1
            elif question_fixed:
                fixed_count += 1

        self.stdout.write("\n" + "=" * 50)
        if apply_fixes:
            self.stdout.write(self.style.SUCCESS(f"Fixed {fixed_count} questions"))
        else:
            self.stdout.write(self.style.NOTICE(f"Would fix {fixed_count} questions (dry run)"))
        
        if error_count:
            self.stdout.write(self.style.WARNING(f"Errors: {error_count} options could not be formatted"))
