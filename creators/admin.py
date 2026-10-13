from django.contrib import admin
from .models import CreatorProfile, Skill, Tool, Specialization
admin.site.register([CreatorProfile, Skill, Tool, Specialization])
