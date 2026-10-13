from django.core.files.base import ContentFile
from django.test import TestCase
from .models import StoredUpload
from .storage import DatabaseMediaStorage


class DatabaseStorageTests(TestCase):
    def test_file_persists_across_storage_instances_and_collision_does_not_overwrite(self):
        first = DatabaseMediaStorage()
        name = first.save('portfolios/1/image.png', ContentFile(b'original'))
        second = DatabaseMediaStorage()
        self.assertEqual(second.open(name).read(), b'original')
        self.assertEqual(second.size(name), 8)
        alternate = second.save(name, ContentFile(b'new'))
        self.assertNotEqual(alternate, name)
        self.assertEqual(first.open(name).read(), b'original')
        second.delete(alternate)
        self.assertFalse(second.exists(alternate))

    def test_evidence_has_no_public_url(self):
        storage = DatabaseMediaStorage()
        name = storage.save('evidence/proof.png', ContentFile(b'private'))
        with self.assertRaises(ValueError):
            storage.url(name)
        self.assertEqual(self.client.get('/media/' + name).status_code, 404)

    def test_size_limit_and_missing_file(self):
        storage = DatabaseMediaStorage()
        with self.assertRaises(ValueError):
            storage.save('portfolios/large.png', ContentFile(b'x' * (5 * 1024 * 1024 + 1)))
        self.assertFalse(StoredUpload.objects.exists())
        with self.assertRaises(FileNotFoundError):
            storage.open('missing.png')
