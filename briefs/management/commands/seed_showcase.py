"""Add explicitly labelled showcase briefs to a chosen brand account."""
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from accounts.models import User
from briefs.models import Brief
from creators.models import Tool, Skill


class Command(BaseCommand):
    help = 'Add two fictional showcase briefs to an existing brand. Never sends invitations.'

    def add_arguments(self, parser):
        parser.add_argument('--brand', required=True, help='Existing brand username')

    @transaction.atomic
    def handle(self, *args, **options):
        brand = User.objects.filter(username=options['brand'], role='BRAND', is_active=True).first()
        if not brand:
            raise CommandError('Choose an existing, active BRAND account.')
        for title, style, content_type, tool, skill in [
            ('DEMO — Orbit fragrance launch', 'Sculptural product', 'PRODUCT', 'Blender', 'Product visualization'),
            ('DEMO — Tomorrow after dark', 'Cinematic sci-fi', 'FILM', 'Runway', 'Cinematic storytelling'),
        ]:
            brief, created = Brief.objects.get_or_create(brand=brand, title=title, defaults={
                'description': 'Fictional hackathon brief. Develop a polished visual concept with a clear generation and finishing workflow.',
                'audience': 'Design-conscious adults', 'deliverables': 'One 15-second concept film and three key visuals.',
                'content_type': content_type, 'style': style, 'aspect_ratio': '16:9',
                'budget_min': 25000, 'budget_max': 60000, 'currency': 'INR',
                'deadline': timezone.localdate() + timedelta(days=30), 'commercial_use': True,
                'usage_requirements': 'Demo only. Before a real campaign, confirm model terms, source provenance, releases, and six months of India social usage.',
                'status': 'ACTIVE',
            })
            if created:
                brief.tools.add(Tool.objects.get_or_create(name=tool)[0])
                brief.skills.add(Skill.objects.get_or_create(name=skill)[0])
        self.stdout.write(self.style.SUCCESS('Showcase briefs ready. Existing briefs were preserved. No invitations sent.'))
