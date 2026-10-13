"""Real concurrent database writes; deliberately PostgreSQL-only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase
from django.utils import timezone
from accounts.models import User
from briefs.models import Brief
from creators.models import CreatorProfile
from .models import Engagement
from .services import transition


@skipUnless(connection.vendor == 'postgresql', 'Requires PostgreSQL concurrent writers')
class ConcurrentTransitionTests(TransactionTestCase):
    def test_same_version_can_only_transition_once(self):
        brand = User.objects.create_user(username='concurrent-brand', email='brand@example.invalid', role='BRAND')
        creator = User.objects.create_user(username='concurrent-creator', email='creator@example.invalid')
        profile = CreatorProfile.objects.create(user=creator, display_name='Concurrent creator')
        brief = Brief.objects.create(brand=brand, title='Concurrent brief', description='Test',
            deliverables='One film', content_type='FILM', style='Cinematic', aspect_ratio='16:9',
            budget_min=10, budget_max=20, deadline=timezone.localdate()+timedelta(days=1))
        engagement = Engagement.objects.create(brief=brief, creator=profile)
        barrier = Barrier(2)

        def attempt():
            close_old_connections()
            try:
                item = Engagement.objects.select_related('brief', 'creator').get(pk=engagement.pk)
                actor = User.objects.get(pk=creator.pk)
                barrier.wait(timeout=10)
                try:
                    transition(item, actor, 'ACCEPTED', version=0)
                    return 'accepted'
                except ValidationError:
                    return 'stale'
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: attempt(), range(2)))
        self.assertCountEqual(results, ['accepted', 'stale'])
        engagement.refresh_from_db()
        self.assertEqual(engagement.version, 1)
        self.assertEqual(engagement.events.count(), 1)
