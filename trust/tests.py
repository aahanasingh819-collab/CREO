from datetime import timedelta
from io import BytesIO
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Permission
from django.utils import timezone
from accounts.models import User
from creators.models import CreatorProfile
from portfolio.models import PortfolioItem
from .models import Evidence

MEMORY_STORAGE = {'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'}, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}


class TrustTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='owner@example.com')
        self.other = User.objects.create_user(username='other', email='other@example.com')
        self.profile = CreatorProfile.objects.create(user=self.owner, display_name='A creator')
        self.project = PortfolioItem.objects.create(creator=self.profile, title='A real project', description='Concept', workflow='Process', style='Cinematic', video_url='https://vimeo.com/123456789')
        self.staff = User.objects.create_user(username='reviewer', email='reviewer@example.com', is_staff=True, role='BRAND')
        self.staff.user_permissions.add(Permission.objects.get(codename='change_evidence'))
        self.evidence = Evidence.objects.create(project=self.project, claim='I built the workflow', explanation='A node graph demonstrates the process', source_url='https://example.com/evidence')

    def review(self, decision='APPROVED', revision=None):
        self.client.force_login(self.staff)
        return self.client.post(reverse('evidence_review', args=[self.evidence.pk]), {'decision': decision, 'note': 'Inspected the supplied process materials.', 'revision': revision or self.project.revision})

    def test_signal_progression_and_project_edit_invalidates_review(self):
        self.assertEqual(self.project.verification_label, 'Evidence Attached')
        self.assertEqual(self.review().status_code, 302)
        self.assertEqual(self.project.verification_label, 'Admin Reviewed')
        self.project.title = 'Changed project'
        self.project.save()
        self.assertEqual(self.project.verification_label, 'Evidence Attached')
        self.assertContains(self.client.get(reverse('review_queue')), 'I built the workflow')

    def test_demo_cannot_receive_reviewed_signal(self):
        self.project.is_demo = True
        self.project.save()
        response = self.review()
        self.assertContains(response, 'Fictional demo work cannot')
        self.evidence.refresh_from_db()
        self.assertEqual(self.evidence.status, 'PENDING')

    def test_permissions_and_self_review(self):
        for user in [self.owner, self.other]:
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('review_queue')).status_code, 403)
            self.assertEqual(self.client.get(reverse('evidence_review', args=[self.evidence.pk])).status_code, 403)
        self.owner.is_staff = True
        self.owner.save()
        self.owner.user_permissions.add(Permission.objects.get(codename='change_evidence'))
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse('evidence_review', args=[self.evidence.pk])).status_code, 403)

    def test_withdraw_removes_signal_and_cannot_be_reviewed(self):
        self.review()
        self.client.force_login(self.owner)
        url = reverse('evidence_withdraw', args=[self.evidence.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(self.project.verification_label, 'Self-declared')
        self.assertContains(self.review(), 'withdrawn')

    def test_stale_review_rejected(self):
        old = self.project.revision
        self.project.save()
        self.assertContains(self.review(revision=old), 'project changed')

    def test_creator_submission_and_injection_ignored(self):
        self.client.force_login(self.owner)
        data = {'claim': 'Source workflow', 'explanation': 'Original node graph', 'source_url': 'https://example.com/proof', 'confirm': 'on', 'status': 'APPROVED', 'reviewer': self.staff.pk}
        response = self.client.post(reverse('evidence_submit', args=[self.project.pk]), data)
        self.assertEqual(response.status_code, 302)
        evidence = Evidence.objects.get(claim='Source workflow')
        self.assertEqual(evidence.status, 'PENDING')
        self.assertIsNone(evidence.reviewer)
        data['source_url'] = 'http://example.com/proof'
        self.assertEqual(self.client.post(reverse('evidence_submit', args=[self.project.pk]), data).status_code, 200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse('evidence_submit', args=[self.project.pk]), data).status_code, 404)

    def test_private_evidence_not_exposed_publicly(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertContains(response, 'Evidence Attached')
        self.assertNotContains(response, self.evidence.source_url)
        self.assertNotContains(response, self.evidence.explanation)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('evidence_file', args=[self.evidence.pk])).status_code, 404)
        self.assertEqual(self.client.get('/media/evidence/anything.png').status_code, 404)

    def test_private_file_access_and_no_store(self):
        from django.core.files.storage import InMemoryStorage
        from unittest.mock import patch
        storage = InMemoryStorage()
        with patch.object(Evidence._meta.get_field('image'), 'storage', storage):
            self.evidence.image = ''
            self.evidence.image.save('proof.png', SimpleUploadedFile('proof.png', b'private bytes'))
            for user in [self.owner, self.staff]:
                self.client.force_login(user)
                response = self.client.get(reverse('evidence_file', args=[self.evidence.pk]))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Cache-Control'], 'private, no-store')
                self.assertEqual(b''.join(response.streaming_content), b'private bytes')

    def test_review_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        self.assertEqual(client.post(reverse('evidence_review', args=[self.evidence.pk]), {}).status_code, 403)
