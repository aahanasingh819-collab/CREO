"""Idempotent fictional catalog. No shared or hardcoded account passwords."""
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from creators.models import CreatorProfile, Skill, Specialization, Tool
from portfolio.models import PortfolioItem

TOOLS = ['Runway', 'Midjourney', 'Blender', 'Kling AI', 'DaVinci Resolve', 'Adobe Firefly', 'ComfyUI', 'Stable Diffusion', 'After Effects', 'Luma']
SKILLS = ['Art direction', 'Animation', 'Cinematic storytelling', 'Compositing', 'Color grading', 'Product visualization', 'Character design', 'Motion design', 'World building', 'Editorial design']
SPECIALTIES = ['AI filmmaking', 'Product campaigns', 'Animation', 'Fashion & beauty', 'Music visuals', 'Architectural worlds']
PEOPLE = [
    ('Aarav Kapoor', 'Mumbai, India', 'Cinematic worlds. Human stories.', 'AI filmmaking', ['Runway', 'Midjourney', 'DaVinci Resolve'], ['Cinematic storytelling', 'Color grading'], 'Violet horizon', 'Cinematic sci-fi'),
    ('Amara Okafor', 'Lagos, Nigeria', 'Impossible products, beautifully imagined.', 'Product campaigns', ['Blender', 'Adobe Firefly', 'After Effects'], ['Product visualization', 'Art direction'], 'Liquid amber', 'Sculptural product'),
    ('Elena Voss', 'Berlin, Germany', 'Architecture from another tomorrow.', 'Architectural worlds', ['Midjourney', 'Blender', 'ComfyUI'], ['World building', 'Compositing'], 'Quiet monuments', 'Architectural minimalism'),
    ('Hana Mori', 'Kyoto, Japan', 'Soft worlds with a surreal point of view.', 'Animation', ['Kling AI', 'Blender', 'After Effects'], ['Animation', 'Character design'], 'Petal dimension', 'Dreamlike pastel'),
    ('Jules Laurent', 'Paris, France', 'Editorial images with an unexpected edge.', 'Fashion & beauty', ['Midjourney', 'Adobe Firefly', 'DaVinci Resolve'], ['Editorial design', 'Art direction'], 'Chrome reverie', 'Futurist editorial'),
    ('Kai Chen', 'Taipei, Taiwan', 'Rhythm, light, and a little controlled chaos.', 'Music visuals', ['ComfyUI', 'Runway', 'After Effects'], ['Motion design', 'Compositing'], 'Signal bloom', 'Neon abstract'),
    ('Leila Haddad', 'Marrakech, Morocco', 'Warm textures. Unfamiliar landscapes.', 'AI filmmaking', ['Luma', 'Midjourney', 'DaVinci Resolve'], ['Cinematic storytelling', 'World building'], 'Dunes of tomorrow', 'Surreal landscape'),
    ('Mateo Silva', 'São Paulo, Brazil', 'Playful animation with serious character.', 'Animation', ['Blender', 'Kling AI', 'After Effects'], ['Animation', 'Character design'], 'Electric playground', 'Playful geometry'),
    ('Mira Sen', 'Bengaluru, India', 'Bold visual systems for ambitious brands.', 'Product campaigns', ['Stable Diffusion', 'ComfyUI', 'Blender'], ['Product visualization', 'Art direction'], 'Emerald frequency', 'Organic luxury'),
    ('Noor Rahman', 'Dhaka, Bangladesh', 'Small details. Expansive stories.', 'AI filmmaking', ['Runway', 'Luma', 'DaVinci Resolve'], ['Cinematic storytelling', 'Color grading'], 'After the rain', 'Atmospheric cinema'),
    ('Sofia Reyes', 'Mexico City, Mexico', 'Color-led storytelling for a brighter world.', 'Fashion & beauty', ['Adobe Firefly', 'Midjourney', 'After Effects'], ['Editorial design', 'Motion design'], 'Solar echoes', 'Chromatic editorial'),
    ('Theo Brooks', 'London, UK', 'Abstract motion that makes you feel something.', 'Music visuals', ['Blender', 'ComfyUI', 'Runway'], ['Motion design', 'Animation'], 'Gravity studies', 'Abstract minimalism'),
    ('Yuna Park', 'Seoul, South Korea', 'Digital objects with a tactile soul.', 'Product campaigns', ['Blender', 'Stable Diffusion', 'Adobe Firefly'], ['Product visualization', 'Compositing'], 'Pearl apparatus', 'Tactile futurism'),
    ('Zara Ali', 'Dubai, UAE', 'Building places that don’t exist. Yet.', 'Architectural worlds', ['Midjourney', 'Luma', 'Blender'], ['World building', 'Art direction'], 'The infinite atrium', 'Speculative architecture'),
]

class Command(BaseCommand):
    help = 'Seed 14 fictional creators and 28 original demo projects. Safe to rerun; never resets existing accounts.'

    @transaction.atomic
    def handle(self, *args, **options):
        tools = {n: Tool.objects.get_or_create(name=n)[0] for n in TOOLS}
        skills = {n: Skill.objects.get_or_create(name=n)[0] for n in SKILLS}
        specs = {n: Specialization.objects.get_or_create(name=n)[0] for n in SPECIALTIES}
        for i, (name, location, headline, specialty, tool_names, skill_names, title, style) in enumerate(PEOPLE):
            username = f'demo_creator_{i + 1:02}'
            user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@example.invalid', 'role': 'CREATOR', 'first_name': name})
            if not created:
                continue  # Never claim or overwrite a preexisting account.
            user.set_unusable_password()
            user.save(update_fields=['password'])
            profile = CreatorProfile.objects.create(user=user, display_name=name, headline=headline, location=location,
                availability=['AVAILABLE', 'AVAILABLE', 'LIMITED', 'AVAILABLE', 'UNAVAILABLE'][i % 5], is_demo=True,
                bio=f'I’m {name.split()[0]}, an independent creative exploring {specialty.lower()} through light, texture, and unexpected visual connections. My practice starts with a clear concept and ends with a considered final frame. I combine iterative image exploration with hands-on composition and finishing.\n\nThis is a fictional creator profile for the CREO prototype. The artwork is original procedural demo media, not evidence of the listed AI capabilities.')
            profile.tools.set([tools[n] for n in tool_names])
            profile.skills.set([skills[n] for n in skill_names])
            profile.specializations.add(specs[specialty])
            for j in range(2):
                asset = Path(settings.BASE_DIR) / 'static' / 'img' / f'demo-{i:02}-{j}.jpg'
                if not asset.exists():
                    raise RuntimeError('Demo assets missing. Run python scripts/generate_art.py first.')
                item = PortfolioItem(creator=profile, title=title if j == 0 else f'{title}: material study',
                    description=f'A fictional concept study exploring {style.lower()}. Original procedural artwork created for this marketplace demo.',
                    format='IMAGE' if j == 0 else 'PRODUCT', aspect_ratio='16:9' if j == 0 else '1:1', style=style, is_demo=True,
                    models_used='Demo concept only — no AI model used for this image',
                    workflow=f'01 / Concept\nExplore {style.lower()} through a restrained palette and a clear focal point.\n\n02 / Form and light\nFor this demo, the image was created with original Python/Pillow procedural geometry: gradients, layered ellipses, atmospheric grain, and perspective lines.\n\n03 / Finish\nCompose the visual, balance contrast, and export a web-ready JPEG. The listed tools illustrate this fictional creator’s proposed toolkit; they were not used to generate this demo asset.',
                    licensing_notes='Original procedural demo artwork supplied with CREO under the project’s MIT license. No client work, stock photography, real endorsements, or verified capability claims are represented.')
                item.image.save(asset.name, ContentFile(asset.read_bytes()), save=False)
                item.save()
                item.tools.set([tools[n] for n in tool_names[:2]])
        self.stdout.write(self.style.SUCCESS(f'Demo catalog ready: {CreatorProfile.objects.filter(is_demo=True).count()} creators, {PortfolioItem.objects.filter(is_demo=True).count()} projects. Demo logins are disabled.'))
