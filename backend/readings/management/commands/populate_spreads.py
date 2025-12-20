import json
from django.core.management.base import BaseCommand
from readings.models import Spread

SPREADS = [
    {
        "name": "single_card",
        "name_cn": "每日一牌",
        "description": "Draw a single card for daily guidance or a quick insight into a specific question.",
        "card_count": 1,
        "positions": ["The Message"],
        "layout": [{"row": 0, "col": 0}]
    },
    {
        "name": "three_card",
        "name_cn": "三牌阵",
        "description": "A classic spread exploring Past, Present, and Future aspects of your question.",
        "card_count": 3,
        "positions": ["The Past", "The Present", "The Future"],
        "layout": [{"row": 0, "col": 0}, {"row": 0, "col": 1}, {"row": 0, "col": 2}]
    },
    {
        "name": "cross",
        "name_cn": "十字牌阵",
        "description": "A five-card spread forming a cross, providing a deeper analysis of your situation.",
        "card_count": 5,
        "positions": [
            "Present Situation",
            "Challenge",
            "Foundation",
            "Past Influence",
            "Future Potential"
        ],
        "layout": [
            {"row": 1, "col": 1},  # Center
            {"row": 0, "col": 1},  # Top
            {"row": 2, "col": 1},  # Bottom
            {"row": 1, "col": 0},  # Left
            {"row": 1, "col": 2}   # Right
        ]
    },
    {
        "name": "celtic_cross",
        "name_cn": "凯尔特十字",
        "description": "The most comprehensive 10-card spread, revealing all aspects of your question with great depth.",
        "card_count": 10,
        "positions": [
            "Present",
            "Challenge",
            "Distant Past",
            "Recent Past",
            "Best Outcome",
            "Near Future",
            "Self",
            "Environment",
            "Hopes & Fears",
            "Final Outcome"
        ],
        "layout": [
            {"row": 2, "col": 1},  # 1 Present
            {"row": 2, "col": 1, "overlay": True},  # 2 Challenge (crosses 1)
            {"row": 4, "col": 1},  # 3 Distant Past
            {"row": 2, "col": 0},  # 4 Recent Past
            {"row": 0, "col": 1},  # 5 Best Outcome
            {"row": 2, "col": 2},  # 6 Near Future
            {"row": 4, "col": 3},  # 7 Self
            {"row": 3, "col": 3},  # 8 Environment
            {"row": 2, "col": 3},  # 9 Hopes & Fears
            {"row": 1, "col": 3}   # 10 Final Outcome
        ]
    },
    {
        "name": "relationship",
        "name_cn": "关系牌阵",
        "description": "A six-card spread designed to explore the dynamics of a relationship.",
        "card_count": 6,
        "positions": [
            "You",
            "Your Partner",
            "The Connection",
            "The Challenge",
            "Advice",
            "Outcome"
        ],
        "layout": [
            {"row": 0, "col": 0},  # You
            {"row": 0, "col": 2},  # Partner
            {"row": 1, "col": 1},  # Connection
            {"row": 2, "col": 1},  # Challenge
            {"row": 3, "col": 0},  # Advice
            {"row": 3, "col": 2}   # Outcome
        ]
    }
]

class Command(BaseCommand):
    help = 'Populate Spread types'

    def handle(self, *args, **options):
        for spread_data in SPREADS:
            Spread.objects.update_or_create(
                name=spread_data['name'],
                defaults=spread_data
            )
            self.stdout.write(f"Created/Updated: {spread_data['name']}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully populated {len(SPREADS)} spreads'))
