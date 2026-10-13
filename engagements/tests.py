from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from creators.models import CreatorProfile
from briefs.models import Brief
from .models import Engagement, EngagementEvent


class EngagementTests(TestCase):
    def setUp(self):
        self.brand = User.objects.create_user(username='brand', email='brand@example.com', role='BRAND')
        self.creator = User.objects.create_user(username='creator', email='creator@example.com')
        self.other = User.objects.create_user(username='other', email='other@example.com', role='BRAND')
        self.profile = CreatorProfile.objects.create(user=self.creator, display_name='Creator')
        self.brief = Brief.objects.create(brand=self.brand, title='Original brief', description='Private creative direction', deliverables='A film', content_type='FILM', style='Cinematic', aspect_ratio='16:9', budget_min=100, budget_max=500, deadline=timezone.localdate()+timedelta(days=20), commercial_use=False, status='ACTIVE')
        self.invite_url = reverse('invite_creator', args=[self.brief.pk, self.profile.pk])

    def invite(self):
        self.client.force_login(self.brand)
        response = self.client.post(self.invite_url, {'message': 'We would love to explore this project with you.', 'share': 'on'})
        self.assertEqual(response.status_code, 302)
        return Engagement.objects.get()

    def step(self, engagement, user, status, **extra):
        engagement.refresh_from_db()
        self.client.force_login(user)
        data = {'status': status, 'version': engagement.version, 'note': 'Project update with rationale.'}
        data.update(extra)
        return self.client.post(engagement.get_absolute_url(), data)

    def test_end_to_end_invitation_delivery_revision_completion(self):
        e = self.invite()
        for user, status in [(self.creator, 'ACCEPTED'), (self.creator, 'IN_PROGRESS'), (self.creator, 'SUBMITTED'),
                             (self.brand, 'IN_PROGRESS'), (self.creator, 'SUBMITTED'), (self.brand, 'COMPLETED')]:
            response = self.step(e, user, status, delivery_url='https://example.com/finished-film')
            self.assertEqual(response.status_code, 302)
        e.refresh_from_db()
        self.assertEqual(e.status, 'COMPLETED')
        self.assertEqual(e.events.count(), 7)
        self.assertContains(self.client.get(e.get_absolute_url()), 'This engagement is closed')
        self.assertContains(self.client.get(reverse('engagement_inbox')), 'Original brief')

    def test_snapshot_is_immutable_and_only_participants_can_read(self):
        e = self.invite()
        self.brief.description = 'New confidential direction'
        self.brief.save()
        self.client.force_login(self.creator)
        response = self.client.get(e.get_absolute_url())
        self.assertContains(response, 'Private creative direction')
        self.assertNotContains(response, 'New confidential direction')
        self.assertEqual(self.client.get(self.brief.get_absolute_url()).status_code, 403)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(e.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.post(e.get_absolute_url(), {}).status_code, 404)

    def test_duplicate_invitation_is_idempotent(self):
        e = self.invite()
        self.invite()
        self.assertEqual(Engagement.objects.count(), 1)
        self.assertEqual(e.events.count(), 1)

    def test_invitation_requires_owner_ready_brief_and_consent(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.invite_url, {}).status_code, 404)
        self.client.force_login(self.creator)
        self.assertEqual(self.client.post(self.invite_url, {}).status_code, 403)
        self.client.force_login(self.brand)
        for status, date in [('DRAFT', timezone.localdate()), ('ACTIVE', timezone.localdate()-timedelta(days=1))]:
            self.brief.status, self.brief.deadline = status, date
            self.brief.save()
            self.assertEqual(self.client.post(self.invite_url, {'message': 'A valid invitation message', 'share': 'on'}).status_code, 200)
        self.assertFalse(Engagement.objects.exists())

    def test_wrong_actor_and_stale_transition_do_not_append_events(self):
        e = self.invite()
        self.assertEqual(self.step(e, self.brand, 'ACCEPTED').status_code, 200)
        self.assertEqual(self.step(e, self.creator, 'ACCEPTED').status_code, 302)
        self.assertEqual(self.step(e, self.creator, 'IN_PROGRESS', version=0).status_code, 200)
        e.refresh_from_db()
        self.assertEqual(e.status, 'ACCEPTED')
        self.assertEqual(e.events.count(), 2)

    def test_delivery_link_and_reasons_validated(self):
        e = self.invite()
        self.assertEqual(self.step(e, self.creator, 'DECLINED', note='').status_code, 200)
        self.step(e, self.creator, 'ACCEPTED')
        self.step(e, self.creator, 'IN_PROGRESS')
        for url in ['', 'http://example.com', 'javascript:alert(1)']:
            self.assertEqual(self.step(e, self.creator, 'SUBMITTED', delivery_url=url).status_code, 200)
        e.refresh_from_db()
        self.assertEqual(e.status, 'IN_PROGRESS')

    def test_decline_and_cancel_are_terminal(self):
        e = self.invite()
        self.assertEqual(self.step(e, self.creator, 'DECLINED').status_code, 302)
        self.assertEqual(self.step(e, self.creator, 'ACCEPTED').status_code, 200)

    def test_brief_with_history_cannot_be_deleted(self):
        self.invite()
        self.assertRedirects(self.client.post(reverse('brief_delete', args=[self.brief.pk])), reverse('brief_edit', args=[self.brief.pk]))
        self.assertTrue(Brief.objects.filter(pk=self.brief.pk).exists())

    def test_invitation_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.brand)
        self.assertEqual(client.post(self.invite_url, {'message': 'Valid invitation', 'share': 'on'}).status_code, 403)
