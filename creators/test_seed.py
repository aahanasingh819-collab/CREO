from io import StringIO
import shutil
import tempfile
from django.core.management import call_command
from django.test import TestCase, override_settings
from accounts.models import User
from creators.models import CreatorProfile
from portfolio.models import PortfolioItem

class SeedTests(TestCase):
    def test_seed_is_repeatable_and_demo_accounts_cannot_login(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        with override_settings(MEDIA_ROOT=directory):
            for _ in range(2):
                call_command('seed_demo', stdout=StringIO())
            self.assertEqual(CreatorProfile.objects.filter(is_demo=True).count(), 14)
            self.assertEqual(PortfolioItem.objects.filter(is_demo=True).count(), 28)
            self.assertTrue(all(not u.has_usable_password() for u in User.objects.all()))
            for item in PortfolioItem.objects.all():
                self.assertTrue(item.image.storage.exists(item.image.name))

    def test_seed_never_claims_existing_account(self):
        user = User.objects.create_user(username='demo_creator_01', email='existing@example.com', role='BRAND')
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        with override_settings(MEDIA_ROOT=directory):
            call_command('seed_demo', stdout=StringIO())
        user.refresh_from_db()
        self.assertEqual(user.role, 'BRAND')
        self.assertFalse(CreatorProfile.objects.filter(user=user).exists())
