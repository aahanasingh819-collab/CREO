import uuid
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from . import ai
from .forms import BriefForm, BuilderForm
from .models import Brief


def brand_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.role != 'BRAND':
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def owned_brief(request, pk):
    return get_object_or_404(Brief.objects.prefetch_related('skills', 'tools', 'specializations'), pk=pk, brand=request.user)


@brand_required
def edit(request, pk=None):
    brief = owned_brief(request, pk) if pk else Brief(brand=request.user)
    draft_id = request.GET.get('draft', '') if not pk else ''
    draft = request.session.get('brief_drafts', {}).get(draft_id)
    if draft and draft.get('user_id') != request.user.pk:
        draft = None
    initial = draft['data'] if draft else None
    form = BriefForm(request.POST if request.method == 'POST' else None, instance=brief, initial=initial)
    if request.method == 'POST' and form.is_valid():
        if draft:
            form.instance.source = draft['source']
        form.save()
        if draft:
            drafts = request.session.get('brief_drafts', {})
            drafts.pop(draft_id, None)
            request.session['brief_drafts'] = drafts
        messages.success(request, 'Brief saved. Explore the creators who fit your vision.')
        return redirect(brief)
    return render(request, 'briefs/form.html', {'form': form, 'brief': brief, 'draft': draft})


@brand_required
def detail(request, pk):
    return render(request, 'briefs/detail.html', {'brief': owned_brief(request, pk)})


@brand_required
def delete(request, pk):
    brief = owned_brief(request, pk)
    if request.method == 'POST':
        try:
            brief.delete()
        except ProtectedError:
            messages.info(request, 'This brief has engagement history. Archive it instead of deleting it.')
            return redirect('brief_edit', pk=brief.pk)
        else:
            messages.success(request, 'Brief removed.')
            return redirect('dashboard')
    return render(request, 'briefs/delete.html', {'brief': brief})


@brand_required
def builder(request):
    form = BuilderForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            if form.cleaned_data['mode'] == 'gemini':
                if not ai.is_configured():
                    raise ai.BuilderError('Gemini is not configured for this demo. Use the local starter or write your brief manually.')
                ai.reserve_attempt(request.user)
                data = ai.generate_draft(form.cleaned_data['idea'])
                source = Brief.Source.GEMINI
            else:
                data = ai.local_draft(form.cleaned_data['idea'])
                source = Brief.Source.LOCAL
        except ai.BuilderError as exc:
            form.add_error(None, str(exc))
        else:
            drafts = request.session.get('brief_drafts', {})
            # Bound session growth and isolate simultaneous tabs with opaque draft IDs.
            drafts = dict(list(drafts.items())[-2:])
            draft_id = uuid.uuid4().hex
            drafts[draft_id] = {'data': data, 'source': source, 'user_id': request.user.pk}
            request.session['brief_drafts'] = drafts
            from django.urls import reverse
            return redirect(reverse('brief_create') + '?draft=' + draft_id)
    return render(request, 'briefs/builder.html', {'form': form, 'gemini_ready': ai.is_configured()})


@brand_required
def matches(request, pk):
    from creators.views import public_profiles
    from discovery.matching import rank_creators
    brief = owned_brief(request, pk)
    matches = rank_creators(brief, public_profiles())
    return render(request, 'briefs/matches.html', {'brief': brief, 'matches': matches})
