from django import forms
from .models import CreatorProfile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CreatorProfile
        fields = ['display_name', 'headline', 'bio', 'location', 'availability', 'specializations', 'skills', 'tools']
        widgets = {'bio': forms.Textarea(attrs={'rows': 5}), 'skills': forms.CheckboxSelectMultiple(),
                   'tools': forms.CheckboxSelectMultiple(), 'specializations': forms.CheckboxSelectMultiple()}
