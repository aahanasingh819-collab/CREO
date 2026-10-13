from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.files.storage import InMemoryStorage
from django.core.files.base import ContentFile
from accounts.models import User
from creators.models import CreatorProfile
from portfolio.models import PortfolioItem


class DeploymentTests(TestCase):
    def test_health(self):
        self.assertEqual(self.client.get('/health/').json(), {'status': 'ok'})

    @override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_public_media_allowlist_and_inactive_creator(self):
        user = User.objects.create_user(username='media-owner')
        profile = CreatorProfile.objects.create(user=user, display_name='Owner')
        project = PortfolioItem.objects.create(creator=profile, title='Image')
        with patch.object(PortfolioItem._meta.get_field('image'), 'storage', InMemoryStorage()):
            project.image = ''
            project.image.save('sample.png', ContentFile(b'image bytes'))
            response = self.client.get(project.image.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'image bytes')
            self.assertEqual(self.client.get('/media/evidence/private.png').status_code, 404)
            self.assertEqual(self.client.get('/media/portfolios/missing.png').status_code, 404)
            user.is_active = False
            user.save()
            self.assertEqual(self.client.get(project.image.url).status_code, 404)
