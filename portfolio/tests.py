from io import BytesIO
import shutil
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from accounts.models import User
from creators.models import CreatorProfile
from .models import PortfolioItem
from .validators import video_embed_url, validate_image

def uploaded_image(fmt='PNG'):
    out = BytesIO()
    Image.new('RGB', (80, 60), '#8655aa').save(out, format=fmt)
    return SimpleUploadedFile('example.' + fmt.lower(), out.getvalue(), content_type='image/' + fmt.lower())

class PortfolioTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(shutil.rmtree, self.media)
        self.user = User.objects.create_user(username='owner', email='owner@example.com')
        self.profile = CreatorProfile.objects.create(user=self.user, display_name='Owner')
        self.other = User.objects.create_user(username='other', email='other@example.com')
        CreatorProfile.objects.create(user=self.other, display_name='Other')
        self.item = PortfolioItem.objects.create(creator=self.profile, title='Original frame', description='A project',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ', style='Cinematic', workflow='Concept then finishing')

    def payload(self, **kwargs):
        data = {'title': 'New frame', 'description': 'A description', 'format': 'IMAGE', 'aspect_ratio': '16:9',
                'style': 'Surreal', 'workflow': 'Original concept, composition, color grade.', 'video_url': 'https://vimeo.com/123456789'}
        data.update(kwargs)
        return data

    def test_create_edit_delete_owner_flow(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('portfolio_create'), self.payload(image=uploaded_image(), creator=self.other.pk))
        self.assertRedirects(response, reverse('dashboard'))
        item = PortfolioItem.objects.get(title='New frame')
        self.assertEqual(item.creator, self.profile)
        self.assertTrue(item.image.storage.exists(item.image.name))
        self.assertContains(self.client.get(item.get_absolute_url()), 'New frame')
        self.assertRedirects(self.client.post(reverse('portfolio_edit', args=[item.pk]), self.payload(title='Updated frame')), reverse('dashboard'))
        item.refresh_from_db()
        self.assertEqual(item.title, 'Updated frame')
        self.assertEqual(self.client.get(reverse('portfolio_delete', args=[item.pk])).status_code, 200)
        self.assertTrue(PortfolioItem.objects.filter(pk=item.pk).exists())
        self.assertRedirects(self.client.post(reverse('portfolio_delete', args=[item.pk])), reverse('dashboard'))
        self.assertFalse(PortfolioItem.objects.filter(pk=item.pk).exists())

    def test_other_creator_cannot_modify(self):
        self.client.force_login(self.other)
        for route in ['portfolio_edit', 'portfolio_delete']:
            url = reverse(route, args=[self.item.pk])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 404)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Original frame')

    def test_brand_denied(self):
        brand = User.objects.create_user(username='brand', email='brand@example.com', role='BRAND')
        self.client.force_login(brand)
        for url in [reverse('portfolio_create'), reverse('portfolio_edit', args=[self.item.pk]), reverse('portfolio_delete', args=[self.item.pk])]:
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)

    def test_anonymous_denied(self):
        self.assertEqual(self.client.post(reverse('portfolio_create'), self.payload()).status_code, 302)

    def test_required_media_and_workflow(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.post(reverse('portfolio_create'), self.payload(video_url='')), 'Add an image or a supported video link')
        self.assertEqual(PortfolioItem.objects.count(), 1)
        self.client.post(reverse('portfolio_create'), self.payload(workflow=''))
        self.assertEqual(PortfolioItem.objects.count(), 1)

    def test_corrupt_and_unsupported_images_rejected(self):
        self.client.force_login(self.user)
        for upload in [SimpleUploadedFile('fake.png', b'not an image', content_type='image/png'), uploaded_image('GIF')]:
            response = self.client.post(reverse('portfolio_create'), self.payload(image=upload))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
        self.assertEqual(PortfolioItem.objects.count(), 1)

    def test_oversized_image_rejected(self):
        image = uploaded_image()
        image.size = 5 * 1024 * 1024 + 1
        with self.assertRaises(ValidationError):
            validate_image(image)

    def test_image_only_and_untrusted_extension(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('portfolio_create'), self.payload(image=uploaded_image(), video_url=''))
        self.assertRedirects(response, reverse('dashboard'))
        item = PortfolioItem.objects.get(title='New frame')
        self.assertTrue(item.image.name.endswith('.png'))
        image = uploaded_image()
        image.name = 'unsafe.html'
        response = self.client.post(reverse('portfolio_create'), self.payload(image=image, video_url=''))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors.get('image'))
        self.assertEqual(PortfolioItem.objects.count(), 2)

    def test_portfolio_title_search(self):
        self.assertContains(self.client.get(reverse('directory'), {'q': 'Original frame'}), 'Owner')

    def test_inactive_owner_project_hidden(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.client.get(self.item.get_absolute_url()).status_code, 404)

    def test_embed_allowlist(self):
        accepted = ['https://youtu.be/dQw4w9WgXcQ', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share', 'https://vimeo.com/123456789']
        for value in accepted:
            self.assertTrue(video_embed_url(value).startswith('https://'))
        rejected = ['javascript:alert(1)', 'http://youtu.be/dQw4w9WgXcQ', 'https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ',
                    'https://evil.test/youtube.com/watch?v=dQw4w9WgXcQ', 'https://user@vimeo.com/123456789', 'https://vimeo.com:8443/123456789',
                    'https://youtu.be/<script>', 'https://vimeo.com/not-a-video']
        for value in rejected:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                video_embed_url(value)

    def test_unsafe_url_rejected_by_form(self):
        self.client.force_login(self.user)
        self.client.post(reverse('portfolio_create'), self.payload(video_url='https://evil.test/video'))
        self.assertEqual(PortfolioItem.objects.count(), 1)

    def test_csrf_delete_protected(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse('portfolio_delete', args=[self.item.pk])).status_code, 403)
        self.assertTrue(PortfolioItem.objects.filter(pk=self.item.pk).exists())

    def test_workflow_is_escaped(self):
        self.item.workflow = '<script>alert(1)</script>'
        self.item.save()
        response = self.client.get(self.item.get_absolute_url())
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;')
