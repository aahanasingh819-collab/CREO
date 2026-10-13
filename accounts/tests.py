from django.test import TestCase, Client
from django.urls import reverse
from .models import User
from creators.models import CreatorProfile

class AuthenticationTests(TestCase):
    def payload(self, role='CREATOR'):
        return {'first_name': 'New Maker', 'username': 'newmaker', 'email': 'maker@example.com', 'role': role,
                'password1': 'Creative-space!891', 'password2': 'Creative-space!891'}

    def test_creator_registration_creates_profile_and_logs_in(self):
        response = self.client.post(reverse('register'), self.payload())
        self.assertRedirects(response, reverse('dashboard'))
        user = User.objects.get(username='newmaker')
        self.assertTrue(user.check_password('Creative-space!891'))
        self.assertEqual(user.creator_profile.display_name, 'New Maker')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_brand_registration_has_no_creator_profile(self):
        self.client.post(reverse('register'), self.payload('BRAND'))
        self.assertFalse(CreatorProfile.objects.exists())
        self.assertContains(self.client.get(reverse('dashboard')), 'BRAND ACCOUNT')

    def test_invalid_role_and_weak_password_rejected(self):
        data = self.payload('ADMIN')
        data.update(password1='123', password2='123')
        self.assertEqual(self.client.post(reverse('register'), data).status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_duplicate_email_case_insensitive(self):
        User.objects.create_user(username='existing', email='Maker@example.com', password='safe-password')
        self.assertContains(self.client.post(reverse('register'), self.payload()), 'already uses this email')
        self.assertEqual(User.objects.count(), 1)

    def test_login_logout_and_safe_next(self):
        User.objects.create_user(username='newmaker', email='maker@example.com', password='Creative-space!891')
        response = self.client.post(reverse('login'), {'username': 'newmaker', 'password': 'Creative-space!891', 'next': 'https://evil.example/'})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_anonymous_dashboard_requires_login(self):
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)

    def test_csrf_registration_required(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post(reverse('register'), self.payload()).status_code, 403)
