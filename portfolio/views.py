from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from creators.models import CreatorProfile
from .forms import PortfolioForm
from .models import PortfolioItem

def detail(request, pk):
    item = get_object_or_404(PortfolioItem.objects.select_related('creator').prefetch_related('tools', 'evidence'), pk=pk, creator__user__is_active=True, creator__user__role='CREATOR')
    return render(request, 'portfolio/detail.html', {'item': item})

@login_required
def edit(request, pk=None):
    if request.user.role != 'CREATOR':
        raise PermissionDenied
    profile, _ = CreatorProfile.objects.get_or_create(user=request.user, defaults={'display_name': request.user.first_name or request.user.username})
    item = get_object_or_404(PortfolioItem, pk=pk, creator=profile) if pk else PortfolioItem(creator=profile)
    form = PortfolioForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        # Save metadata and tool relationships together before any reviewer can
        # approve this revision. PostgreSQL holds the row lock until commit.
        with transaction.atomic():
            form.save()
        messages.success(request, 'Your work is live on your portfolio.')
        return redirect('dashboard')
    return render(request, 'form.html', {'form': form, 'eyebrow': 'THE WORK SPEAKS', 'title': 'Edit your project.' if pk else 'Add something remarkable.', 'description': 'Go beyond the final frame. Show brands how you made it.', 'button': 'Save project'})

@login_required
def delete(request, pk):
    if request.user.role != 'CREATOR':
        raise PermissionDenied
    item = get_object_or_404(PortfolioItem, pk=pk, creator__user=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Project removed from your portfolio.')
        return redirect('dashboard')
    return render(request, 'portfolio/delete.html', {'item': item})
