from django import forms
from creators.models import Tool, Skill, Specialization, CreatorProfile
from portfolio.models import PortfolioItem


class DiscoveryForm(forms.Form):
    q = forms.CharField(required=False, max_length=120, label='Keyword', widget=forms.TextInput(attrs={'placeholder': 'Name, skill, tool, or project…'}))
    skill = forms.ModelChoiceField(required=False, queryset=Skill.objects.all(), empty_label='Any skill')
    tool = forms.ModelChoiceField(required=False, queryset=Tool.objects.all(), empty_label='Any tool')
    specialization = forms.ModelChoiceField(required=False, queryset=Specialization.objects.all(), empty_label='Any specialization')
    format = forms.ChoiceField(required=False, choices=[('', 'Any format')] + list(PortfolioItem.Format.choices))
    style = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'placeholder': 'e.g. cinematic'}))
    aspect = forms.ChoiceField(required=False, choices=[('', 'Any aspect ratio')] + list(PortfolioItem.Aspect.choices))
    availability = forms.ChoiceField(required=False, choices=[('', 'Any availability')] + list(CreatorProfile.Availability.choices))
