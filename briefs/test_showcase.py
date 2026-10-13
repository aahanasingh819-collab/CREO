from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from accounts.models import User
from .models import Brief


class ShowcaseTests(TestCase):
    def test_seed_is_explicit_idempotent_and_preserves_edits(self):
        User.objects.create_user(username='showcase-brand', role='BRAND')
        for _ in range(2):
            call_command('seed_showcase', brand='showcase-brand', stdout=StringIO())
        self.assertEqual(Brief.objects.count(), 2)
        brief = Brief.objects.first()
        brief.description = 'Edited by the brand'
        brief.save()
        call_command('seed_showcase', brand='showcase-brand', stdout=StringIO())
        brief.refresh_from_db()
        self.assertEqual(brief.description, 'Edited by the brand')

    def test_seed_rejects_missing_or_creator_account(self):
        User.objects.create_user(username='creator')
        for username in ['missing', 'creator']:
            with self.assertRaises(CommandError):
                call_command('seed_showcase', brand=username)
