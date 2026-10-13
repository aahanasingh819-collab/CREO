import uuid
from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator, URLValidator
from django.db import models
from portfolio.validators import validate_image


def evidence_storage():
    if settings.DATABASE_MEDIA:
        from portfolio.storage import DatabaseMediaStorage
        return DatabaseMediaStorage()
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)


def evidence_path(instance, filename):
    return f'evidence/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'


class Evidence(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Awaiting review'
        APPROVED = 'APPROVED', 'Admin reviewed'
        REJECTED = 'REJECTED', 'Changes requested'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    project = models.ForeignKey('portfolio.PortfolioItem', on_delete=models.CASCADE, related_name='evidence')
    claim = models.CharField(max_length=160, help_text='The specific workflow or tool-use claim this supports.')
    explanation = models.TextField(max_length=2000)
    image = models.ImageField(upload_to=evidence_path, storage=evidence_storage, blank=True,
                              validators=[validate_image, FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])])
    source_url = models.URLField(blank=True, validators=[URLValidator(schemes=['https'])])
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='evidence_reviews')
    review_note = models.TextField(max_length=1500, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_revision = models.DateTimeField(null=True, blank=True)
    reviewed_version = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    @property
    def current_approval(self):
        return self.status == self.Status.APPROVED and self.reviewed_version == self.project.revision

    @property
    def display_status(self):
        if self.status == self.Status.APPROVED and not self.current_approval:
            return 'Project changed — review needed'
        return self.get_status_display()
