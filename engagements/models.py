from django.conf import settings
from django.db import models
from django.urls import reverse


class Engagement(models.Model):
    class Status(models.TextChoices):
        INVITED = 'INVITED', 'Invited'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'
        IN_PROGRESS = 'IN_PROGRESS', 'In progress'
        SUBMITTED = 'SUBMITTED', 'Submitted for review'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    brief = models.ForeignKey('briefs.Brief', on_delete=models.PROTECT, related_name='engagements')
    creator = models.ForeignKey('creators.CreatorProfile', on_delete=models.PROTECT, related_name='engagements')
    brief_snapshot = models.JSONField(default=dict, editable=False)
    message = models.TextField(max_length=2000)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.INVITED, db_index=True)
    version = models.PositiveIntegerField(default=0)
    delivery_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-pk']
        constraints = [models.UniqueConstraint(fields=['brief', 'creator'], name='one_invitation_per_brief_creator')]

    def get_absolute_url(self):
        return reverse('engagement_detail', args=[self.pk])


class EngagementEvent(models.Model):
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=15, choices=Engagement.Status.choices)
    note = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']
