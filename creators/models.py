from django.conf import settings
from django.db import models
from django.urls import reverse


class Taxonomy(models.Model):
    name = models.CharField(max_length=80, unique=True)
    class Meta:
        abstract = True
        ordering = ['name']
    def __str__(self):
        return self.name

class Skill(Taxonomy):
    pass

class Tool(Taxonomy):
    pass

class Specialization(Taxonomy):
    pass


class CreatorProfile(models.Model):
    class Availability(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available for work'
        LIMITED = 'LIMITED', 'Limited availability'
        UNAVAILABLE = 'UNAVAILABLE', 'Currently booked'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='creator_profile')
    display_name = models.CharField(max_length=120)
    headline = models.CharField(max_length=160, blank=True)
    bio = models.TextField(max_length=3000, blank=True)
    location = models.CharField(max_length=100, blank=True)
    availability = models.CharField(max_length=15, choices=Availability.choices, default=Availability.AVAILABLE, db_index=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name='creators')
    tools = models.ManyToManyField(Tool, blank=True, related_name='creators')
    specializations = models.ManyToManyField(Specialization, blank=True, related_name='creators')
    is_demo = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_name', 'pk']
    def __str__(self):
        return self.display_name
    def get_absolute_url(self):
        return reverse('creator_detail', args=[self.pk])
    @property
    def initials(self):
        return ''.join(p[0] for p in self.display_name.split()[:2]).upper()

    @property
    def verification_label(self):
        labels = {item.verification_label for item in self.portfolio_items.all()}
        if 'Admin Reviewed' in labels:
            return 'Admin Reviewed'
        return 'Evidence Attached' if 'Evidence Attached' in labels else 'Self-declared'
