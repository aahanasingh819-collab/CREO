from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.http import require_GET
from portfolio.models import PortfolioItem


@require_GET
def health(request):
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})


@require_GET
def public_media(request, name):
    # Public files must belong to a currently visible portfolio record. No arbitrary paths.
    item = PortfolioItem.objects.filter(image=name, creator__user__is_active=True, creator__user__role='CREATOR').first()
    if not item:
        raise Http404
    try:
        response = FileResponse(item.image.open('rb'))
    except (FileNotFoundError, ValueError):
        raise Http404
    response['Cache-Control'] = 'public, max-age=60'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
