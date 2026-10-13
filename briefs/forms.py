from django import forms
from django.utils import timezone
from .models import Brief


class BriefForm(forms.ModelForm):
    class Meta:
        model = Brief
        fields = ['title', 'description', 'audience', 'deliverables', 'content_type', 'style', 'aspect_ratio',
                  'budget_min', 'budget_max', 'currency', 'deadline', 'commercial_use', 'usage_requirements',
                  'skills', 'tools', 'specializations', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}), 'deliverables': forms.Textarea(attrs={'rows': 3}),
            'usage_requirements': forms.Textarea(attrs={'rows': 3}), 'deadline': forms.DateInput(attrs={'type': 'date'}),
            'skills': forms.CheckboxSelectMultiple(), 'tools': forms.CheckboxSelectMultiple(),
            'specializations': forms.CheckboxSelectMultiple(),
        }
        labels = {'tools': 'Preferred tools (optional)', 'skills': 'Required skills (optional)',
                  'specializations': 'Preferred specializations (optional)', 'commercial_use': 'Intended for commercial use'}

    def clean_deadline(self):
        date = self.cleaned_data['deadline']
        # An unchanged historic deadline must not block archiving or editing an old brief.
        if date < timezone.localdate() and (not self.instance.pk or date != self.instance.deadline):
            raise forms.ValidationError('Choose today or a future deadline.')
        return date


class BuilderForm(forms.Form):
    idea = forms.CharField(min_length=20, max_length=4000, label='What are you imagining?',
                           widget=forms.Textarea(attrs={'rows': 6, 'placeholder': 'A surreal product campaign for a new coffee brand. Warm amber light, 3 vertical stills for Instagram…'}))
    mode = forms.ChoiceField(choices=[('local', 'Local starter — no external service'), ('gemini', 'Generate with Gemini')])
    consent = forms.BooleanField(required=False, label='Send this idea to Google Gemini to generate an editable draft.',
                                 help_text='Use non-confidential ideas. Free-tier submissions may be used by Google to improve its products.')

    def clean(self):
        data = super().clean()
        if data.get('mode') == 'gemini' and not data.get('consent'):
            self.add_error('consent', 'Confirm before sending your idea to Gemini, or use the local starter.')
        return data
