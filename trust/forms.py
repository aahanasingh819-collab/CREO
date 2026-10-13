from django import forms
from .models import Evidence


class EvidenceForm(forms.ModelForm):
    confirm = forms.BooleanField(label='I have permission to share this proof with CREO reviewers and have removed secrets and personal information.')

    class Meta:
        model = Evidence
        fields = ['claim', 'explanation', 'image', 'source_url']
        widgets = {'explanation': forms.Textarea(attrs={'rows': 4})}
        help_texts = {'image': 'Private reviewer screenshot. JPEG, PNG, or WebP, up to 5 MB.',
                      'source_url': 'Optional HTTPS evidence link. Reviewers open links manually; CREO does not fetch them.'}

    def clean(self):
        data = super().clean()
        if not data.get('image') and not data.get('source_url'):
            raise forms.ValidationError('Attach a screenshot or provide an HTTPS evidence link.')
        return data


class ReviewForm(forms.Form):
    decision = forms.ChoiceField(choices=[('APPROVED', 'Mark claim reviewed'), ('REJECTED', 'Request changes')])
    note = forms.CharField(max_length=1500, widget=forms.Textarea(attrs={'rows': 4}), label='Review rationale')
    revision = forms.IntegerField(min_value=1, widget=forms.HiddenInput())
