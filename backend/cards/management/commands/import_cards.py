import re
from pathlib import Path
from django.core.management.base import BaseCommand
from cards.models import TarotCard, Suit, Arcana

# Data map to help parse the JS file content roughly
# or just a hardcoded list mapping if the JS parsing is too brittle.
# Since I have the content, I can actually just put the list here directly in the python script 
# but that's a lot of text. I'll read the file.

class Command(BaseCommand):
    help = 'Import Tarot cards from the raw JS file source'

    def handle(self, *args, **options):
        # Path to the JS file
        js_path = Path(__file__).resolve().parents[2] / 'data' / 'cardRoutes.js'

        if not js_path.exists():
            self.stdout.write(self.style.ERROR(f'Card data file not found: {js_path}'))
            return
        
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract the array content using regex
        # Looking for const tarotCards = [ ... ];
        match = re.search(r'const tarotCards = \[(.*?)\];', content, re.DOTALL)
        if not match:
            self.stdout.write(self.style.ERROR('Could not find tarotCards array'))
            return

        array_content = match.group(1)
        
        # This is a JS object array, keys are not quoted. We need to make it JSON compliant or parse it manually.
        # "name": "The Fool", description: "...", image: "..."
        # I'll use regex to iterate over objects.
        
        # Regex to find each object: { ... }
        # This is simple because the structure is consistent in the file I viewed.
        card_pattern = re.compile(r'{\s*name:\s*"(.*?)",\s*description:\s*"(.*?)",\s*image:\s*"(.*?)"\s*,?\s*}', re.DOTALL)
        
        cards_found = card_pattern.findall(array_content)
        
        self.stdout.write(f"Found {len(cards_found)} cards via regex.")
        
        arcana_map = {
            'The Fool': (0, Arcana.MAJOR, Suit.NONE),
            'The Magician': (1, Arcana.MAJOR, Suit.NONE),
            'The High Priestess': (2, Arcana.MAJOR, Suit.NONE),
            'The Empress': (3, Arcana.MAJOR, Suit.NONE),
            'The Emperor': (4, Arcana.MAJOR, Suit.NONE),
            'The Hierophant': (5, Arcana.MAJOR, Suit.NONE),
            'The Lovers': (6, Arcana.MAJOR, Suit.NONE),
            'The Chariot': (7, Arcana.MAJOR, Suit.NONE),
            'Strength': (8, Arcana.MAJOR, Suit.NONE),
            'The Hermit': (9, Arcana.MAJOR, Suit.NONE),
            'Wheel of Fortune': (10, Arcana.MAJOR, Suit.NONE),
            'Justice': (11, Arcana.MAJOR, Suit.NONE),
            'The Hanged Man': (12, Arcana.MAJOR, Suit.NONE),
            'Death': (13, Arcana.MAJOR, Suit.NONE),
            'Temperance': (14, Arcana.MAJOR, Suit.NONE),
            'The Devil': (15, Arcana.MAJOR, Suit.NONE),
            'The Tower': (16, Arcana.MAJOR, Suit.NONE),
            'The Star': (17, Arcana.MAJOR, Suit.NONE),
            'The Moon': (18, Arcana.MAJOR, Suit.NONE),
            'The Sun': (19, Arcana.MAJOR, Suit.NONE),
            'Judgement': (20, Arcana.MAJOR, Suit.NONE),
            'The World': (21, Arcana.MAJOR, Suit.NONE),
        }
        
        def get_minor_info(name):
            # name e.g. "Ace of Wands", "Page of Cups"
            parts = name.split(' of ')
            if len(parts) != 2:
                return 0, Suit.NONE
                
            rank = parts[0]
            suit_str = parts[1]
            
            suit_map = {
                'Wands': Suit.WANDS,
                'Cups': Suit.CUPS,
                'Swords': Suit.SWORDS,
                'Pentacles': Suit.PENTACLES
            }
            suit = suit_map.get(suit_str, Suit.NONE)
            
            rank_map = {
                'Ace': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 
                'Six': 6, 'Seven': 7, 'Eight': 8, 'Nine': 9, 'Ten': 10,
                'Page': 11, 'Knight': 12, 'Queen': 13, 'King': 14
            }
            number = rank_map.get(rank, 0)
            return number, suit

        for name, desc, img_path in cards_found:
            # Clean up logic
            # img_path is like /tarotdeck/thefool.jpeg -> we want just 'thefool.jpeg' or logical path
            filename = img_path.split('/')[-1]
            
            if name in arcana_map:
                number, arcana, suit = arcana_map[name]
            else:
                arcana = Arcana.MINOR
                number, suit = get_minor_info(name)
            
            # Create or update
            TarotCard.objects.update_or_create(
                name=name,
                defaults={
                    'number': number,
                    'arcana': arcana,
                    'suit': suit,
                    'img': filename,
                    'meanings_light': [desc.strip()], # Using the description as the meaning
                    'keywords': [] # Can extract from description lightly later if needed
                }
            )
            
        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(cards_found)} cards'))
