from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from portfolio.models import PortfolioItem
from .models import Evidence
from .forms import EvidenceForm, ReviewForm


def can_review(user):
    return user.is_staff and user.has_perm('trust.change_evidence')


@login_required
def submit(request, pk):
    if request.user.role != 'CREATOR':
        raise PermissionDenied
    project = get_object_or_404(PortfolioItem, pk=pk, creator__user=request.user)
    form = EvidenceForm(request.POST if request.method == 'POST' else None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        evidence = form.save(commit=False)
        evidence.project = project
        evidence.save()
        messages.success(request, 'Evidence attached. An authorized reviewer can now assess this specific claim.')
        return redirect('evidence_list')
    return render(request, 'trust/submit.html', {'form': form, 'project': project})


@login_required
def mine(request):
    if request.user.role != 'CREATOR':
        raise PermissionDenied
    return render(request, 'trust/mine.html', {'evidence': Evidence.objects.filter(project__creator__user=request.user).select_related('project'),
                                            'projects': PortfolioItem.objects.filter(creator__user=request.user)})


@login_required
def file(request, pk):
    evidence = get_object_or_404(Evidence.objects.select_related('project__creator'), pk=pk)
    if request.user.pk != evidence.project.creator.user_id and not can_review(request.user):
        raise Http404
    if not evidence.image:
        raise Http404
    try:
        response = FileResponse(evidence.image.open('rb'), as_attachment=True, filename='evidence' + evidence.image.name[evidence.image.name.rfind('.'):])
    except FileNotFoundError:
        raise Http404
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
@require_POST
def withdraw(request, pk):
    evidence = get_object_or_404(Evidence, pk=pk, project__creator__user=request.user)
    Evidence.objects.filter(pk=evidence.pk).update(status=Evidence.Status.WITHDRAWN)
    messages.success(request, 'Evidence withdrawn. It no longer contributes a public trust signal.')
    return redirect('evidence_list')


@login_required
@permission_required('trust.change_evidence', raise_exception=True)
def queue(request):
    if not can_review(request.user):
        raise PermissionDenied
    entries = Evidence.objects.filter(Q(status='PENDING') | Q(status='APPROVED') & ~Q(reviewed_version=F('project__revision'))).select_related('project__creator')
    return render(request, 'trust/queue.html', {'entries': entries})


@login_required
@permission_required('trust.change_evidence', raise_exception=True)
def review(request, pk):
    if not can_review(request.user):
        raise PermissionDenied
    evidence = get_object_or_404(Evidence.objects.select_related('project__creator'), pk=pk)
    if evidence.project.creator.user_id == request.user.pk:
        raise PermissionDenied('You cannot review your own evidence.')
    form = ReviewForm(request.POST if request.method == 'POST' else None, initial={'revision': evidence.project.revision})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            # Lock the project first so an edit cannot race with approval on PostgreSQL.
            project = PortfolioItem.objects.select_for_update().get(pk=evidence.project_id)
            current = Evidence.objects.select_for_update().get(pk=pk)
            if current.status == 'WITHDRAWN':
                form.add_error(None, 'This evidence was withdrawn.')
            elif project.revision != form.cleaned_data['revision']:
                form.add_error(None, 'The project changed. Reload and review the current version.')
            elif form.cleaned_data['decision'] == 'APPROVED' and (project.is_demo or project.creator.is_demo):
                form.add_error(None, 'Fictional demo work cannot receive an Admin Reviewed signal.')
            else:
                current.status = form.cleaned_data['decision']
                current.review_note = form.cleaned_data['note']
                current.reviewer = request.user
                current.reviewed_at = timezone.now()
                current.reviewed_revision = project.updated_at
                current.reviewed_version = project.revision
                current.save()
                messages.success(request, 'Review recorded for this project revision.')
                return redirect('review_queue')
    return render(request, 'trust/review.html', {'evidence': evidence, 'form': form})
