from django import forms
from .models import PortfolioItem

class PortfolioForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = ['title', 'description', 'image', 'video_url', 'format', 'aspect_ratio', 'style', 'tools', 'models_used', 'workflow', 'licensing_notes']
        widgets = {'description': forms.Textarea(attrs={'rows': 3}), 'workflow': forms.Textarea(attrs={'rows': 5}),
                   'licensing_notes': forms.Textarea(attrs={'rows': 3}), 'tools': forms.CheckboxSelectMultiple()}
        help_texts = {'image': 'JPEG, PNG or WebP. Up to 5 MB. Upload only media you have rights to share.',
                      'video_url': 'HTTPS YouTube watch/share or public Vimeo links. The host must permit embedding.'}
