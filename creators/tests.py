from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from .models import CreatorProfile, Tool, Skill, Specialization

class CreatorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='maker', email='maker@example.com', password='Creative-space!891')
        cls.profile = CreatorProfile.objects.create(user=cls.user, display_name='Mira Example', headline='Unusual worlds', bio='Cinematic imagination')
        cls.tool = Tool.objects.create(name='Runway')
        cls.skill = Skill.objects.create(name='Compositing')
        cls.specialty = Specialization.objects.create(name='Architecture')
        cls.profile.tools.add(cls.tool)
        cls.profile.skills.add(cls.skill)
        cls.profile.specializations.add(cls.specialty)

    def test_search_fields(self):
        for q in ['Mira', 'unusual', 'cinematic', 'Runway', 'Compositing', 'Architecture']:
            with self.subTest(q=q):
                self.assertContains(self.client.get(reverse('directory'), {'q': q}), 'Mira Example')

    def test_empty_and_escaped_search(self):
        response = self.client.get(reverse('directory'), {'q': '<script>alert(1)</script>'})
        self.assertContains(response, 'No creators matched')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_pagination_stable_and_invalid_page_handled(self):
        for i in range(12):
            user = User.objects.create_user(username=f'extra{i}', email=f'extra{i}@example.com')
            CreatorProfile.objects.create(user=user, display_name=f'Creator {i:02}')
        first = self.client.get(reverse('directory'))
        self.assertEqual(len(first.context['page_obj']), 9)
        second = self.client.get(reverse('directory'), {'page': 2})
        self.assertEqual(len(second.context['page_obj']), 4)
        self.assertFalse(set(p.pk for p in first.context['page_obj']) & set(p.pk for p in second.context['page_obj']))
        self.assertEqual(self.client.get(reverse('directory'), {'page': 'bad'}).status_code, 200)

    def test_htmx_fragment(self):
        response = self.client.get(reverse('directory'), {'q': 'Runway'}, HTTP_HX_REQUEST='true')
        self.assertContains(response, 'Mira Example')
        self.assertNotContains(response, '<!doctype html>')
        self.assertIn('HX-Request', response.headers['Vary'])

    def test_profile_edit_persists_and_ignores_owner_injection(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile_edit'), {'display_name': 'Updated Maker', 'headline': 'Hello', 'bio': 'My bio',
            'location': 'Mumbai', 'availability': 'LIMITED', 'tools': [self.tool.pk], 'skills': [self.skill.pk], 'specializations': [self.specialty.pk], 'is_demo': True, 'user': 999})
        self.assertRedirects(response, reverse('dashboard'))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.display_name, 'Updated Maker')
        self.assertEqual(self.profile.user_id, self.user.pk)
        self.assertFalse(self.profile.is_demo)
        self.assertEqual(self.profile.tools.count(), 1)

    def test_brand_cannot_edit_creator_profile(self):
        brand = User.objects.create_user(username='brand', email='brand@example.com', role='BRAND')
        self.client.force_login(brand)
        self.assertEqual(self.client.get(reverse('profile_edit')).status_code, 403)
        self.assertEqual(self.client.post(reverse('profile_edit'), {}).status_code, 403)

    def test_inactive_profiles_hidden(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.get(self.profile.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(reverse('directory')), 'Mira Example')

    def test_taxonomy_api(self):
        response = self.client.get(reverse('taxonomy'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['tools'][0]['name'], 'Runway')

    def test_public_pages_render(self):
        for url in [reverse('home'), reverse('directory'), self.profile.get_absolute_url(), reverse('login'), reverse('register')]:
            self.assertEqual(self.client.get(url).status_code, 200)
