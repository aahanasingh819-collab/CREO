import uuid
from pathlib import Path
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from .validators import validate_image, validate_video_url, video_embed_url


class StoredUpload(models.Model):
    """Small prototype uploads; access is controlled by portfolio/evidence views."""
    name = models.CharField(max_length=255, primary_key=True)
    content = models.BinaryField()
    byte_size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

def image_path(instance, filename):
    # Restrict even direct storage calls to passive image extensions.
    suffix = Path(filename).suffix.lower()
    if suffix not in {'.png', '.jpg', '.jpeg', '.webp'}:
        suffix = '.img'
    return f'portfolios/{instance.creator_id}/{uuid.uuid4().hex}{suffix}'

class PortfolioItem(models.Model):
    class Format(models.TextChoices):
        IMAGE = 'IMAGE', 'Image / key visual'
        FILM = 'FILM', 'AI film'
        ANIMATION = 'ANIMATION', 'Animation'
        PRODUCT = 'PRODUCT', 'Product campaign'
    class Aspect(models.TextChoices):
        WIDE = '16:9', '16:9 — Landscape'
        VERTICAL = '9:16', '9:16 — Vertical'
        SQUARE = '1:1', '1:1 — Square'
        CINEMA = '21:9', '21:9 — Cinematic'
        PORTRAIT = '4:5', '4:5 — Portrait'
    creator = models.ForeignKey('creators.CreatorProfile', on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=140)
    description = models.TextField(max_length=2000)
    image = models.ImageField(upload_to=image_path, validators=[validate_image], blank=True)
    video_url = models.URLField(blank=True, validators=[validate_video_url])
    format = models.CharField(max_length=15, choices=Format.choices, default=Format.IMAGE, db_index=True)
    aspect_ratio = models.CharField(max_length=5, choices=Aspect.choices, default=Aspect.WIDE)
    style = models.CharField(max_length=100)
    tools = models.ManyToManyField('creators.Tool', related_name='portfolio_items', blank=True)
    models_used = models.CharField(max_length=250, blank=True, help_text='Optional model names and versions.')
    workflow = models.TextField(max_length=5000, help_text='Describe your concept, generation, editing, and finishing process.')
    licensing_notes = models.TextField(max_length=1500, blank=True, help_text='Self-reported source and usage information; not legal certification.')
    is_demo = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revision = models.PositiveIntegerField(default=1, editable=False)
    class Meta:
        ordering = ['-created_at', '-pk']
    def clean(self):
        if not self.image and not self.video_url:
            raise ValidationError('Add an image or a supported video link.')
        if self.creator_id and self.creator.user.role != 'CREATOR':
            raise ValidationError('Only creators can own portfolio work.')
    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if not self._state.adding:
            self.revision = models.F('revision') + 1
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'revision', 'updated_at'}
        super().save(*args, **kwargs)
        if not isinstance(self.revision, int):
            self.refresh_from_db(fields=['revision'])
    def get_absolute_url(self):
        return reverse('portfolio_detail', args=[self.pk])
    @property
    def embed_url(self):
        return video_embed_url(self.video_url)

    @property
    def verification_label(self):
        evidence = [e for e in self.evidence.all() if e.status in {'PENDING', 'APPROVED'}]
        if not self.is_demo and not self.creator.is_demo and any(e.current_approval for e in evidence):
            return 'Admin Reviewed'
        return 'Evidence Attached' if evidence else 'Self-declared'
