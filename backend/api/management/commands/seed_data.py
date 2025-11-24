from django.core.management.base import BaseCommand
from api.models import Recipe, Ingredient, RecipeStep, RecipeIngredient
from django.core.files.base import ContentFile
import requests
import os

class Command(BaseCommand):
    help = 'Seeds the database with initial data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')
        
        # Helper to download image
        def save_image_from_url(model_instance, field_name, url, filename):
            try:
                self.stdout.write(f'Downloading {filename}...')
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    getattr(model_instance, field_name).save(filename, ContentFile(response.content), save=True)
                    self.stdout.write(f'Saved {filename}')
                else:
                    self.stdout.write(self.style.WARNING(f'Failed to download {url}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error downloading {url}: {e}'))

        # Clean up
        Recipe.objects.all().delete()
        Ingredient.objects.all().delete()
        
        # Ingredients with stock quantities
        pork = Ingredient.objects.create(name='五花肉', quantity=500, unit='g')
        sugar = Ingredient.objects.create(name='冰糖', quantity=100, unit='g')
        soy_sauce = Ingredient.objects.create(name='生抽', quantity=0, unit='ml')  # Out of stock
        broccoli = Ingredient.objects.create(name='西蓝花', quantity=2, unit='pc')
        shrimp = Ingredient.objects.create(name='虾仁', quantity=0, unit='g')  # Out of stock
        garlic = Ingredient.objects.create(name='蒜末', quantity=50, unit='g')
        
        # Recipe 1: Red Braised Pork
        r1 = Recipe.objects.create(
            title='经典红烧肉',
            description='肥而不腻，入口即化，是下饭神菜。',
            cooking_time=90,
            category='硬菜',
        )
        save_image_from_url(r1, 'cover_image', 'https://images.unsplash.com/photo-1617093727343-374698b1b08d?q=80&w=800&auto=format&fit=crop', 'red_braised_pork.jpg')
        
        RecipeIngredient.objects.create(recipe=r1, ingredient=pork, amount=500, quantity_display='500g')
        RecipeIngredient.objects.create(recipe=r1, ingredient=sugar, amount=30, quantity_display='30g')
        RecipeIngredient.objects.create(recipe=r1, ingredient=soy_sauce, amount=30, quantity_display='2勺')
        
        s1_1 = RecipeStep.objects.create(recipe=r1, step_number=1, description='五花肉切块，冷水下锅焯水去腥。')
        save_image_from_url(s1_1, 'image', 'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?q=80&w=800&auto=format&fit=crop', 'step1_pork.jpg')

        s1_2 = RecipeStep.objects.create(recipe=r1, step_number=2, description='锅中不放油，放入五花肉煸炒出油脂，表面微焦盛出。')
        save_image_from_url(s1_2, 'image', 'https://images.unsplash.com/photo-1512058564366-18510be2db19?q=80&w=800&auto=format&fit=crop', 'step2_fry.jpg')

        RecipeStep.objects.create(recipe=r1, step_number=3, description='锅留底油炒糖色，放入肉块翻炒均匀，加入开水没过肉块，小火炖煮1小时。')
        RecipeStep.objects.create(recipe=r1, step_number=4, description='大火收汁，装盘即可。')
        
        # Recipe 2: Broccoli with Shrimp
        r2 = Recipe.objects.create(
            title='蒜蓉西蓝花炒虾仁',
            description='清淡健康，低脂美味。',
            cooking_time=20,
            category='快手菜',
        )
        save_image_from_url(r2, 'cover_image', 'https://images.unsplash.com/photo-1623961990059-284327f929e6?q=80&w=800&auto=format&fit=crop', 'broccoli_shrimp.jpg')
        
        RecipeIngredient.objects.create(recipe=r2, ingredient=broccoli, amount=1, quantity_display='1颗')
        RecipeIngredient.objects.create(recipe=r2, ingredient=shrimp, amount=200, quantity_display='200g')
        RecipeIngredient.objects.create(recipe=r2, ingredient=garlic, amount=15, quantity_display='3瓣')
        
        RecipeStep.objects.create(recipe=r2, step_number=1, description='西蓝花洗净掰成小朵，焯水备用。')
        RecipeStep.objects.create(recipe=r2, step_number=2, description='虾仁去虾线，加少许料酒腌制。')
        RecipeStep.objects.create(recipe=r2, step_number=3, description='热锅凉油爆香蒜末，加入虾仁变色，放入西蓝花翻炒均匀。')
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded data'))
