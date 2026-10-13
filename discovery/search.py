from django.db.models import Q


def filter_profiles(profiles, data):
    q = data.get('q', '')
    if q:
        profiles = profiles.filter(Q(display_name__icontains=q) | Q(headline__icontains=q) | Q(bio__icontains=q) |
                                   Q(skills__name__icontains=q) | Q(tools__name__icontains=q) |
                                   Q(specializations__name__icontains=q) | Q(portfolio_items__title__icontains=q))
    for name in ['skill', 'specialization']:
        if data.get(name):
            profiles = profiles.filter(**{name + 's': data[name]})
    if data.get('tool'):
        profiles = profiles.filter(Q(tools=data['tool']) | Q(portfolio_items__tools=data['tool']))
    if data.get('availability'):
        profiles = profiles.filter(availability=data['availability'])
    # One filter call requires format/style/aspect to match the SAME portfolio entry.
    entry = {}
    for key, lookup in [('format', 'format'), ('style', 'style__icontains'), ('aspect', 'aspect_ratio')]:
        if data.get(key):
            entry['portfolio_items__' + lookup] = data[key]
    if entry:
        profiles = profiles.filter(**entry)
    return profiles.distinct()


def relaxation_suggestions(profiles, data, params):
    suggestions = []
    for field, value in data.items():
        if not value:
            continue
        relaxed = dict(data)
        relaxed[field] = ''
        count = filter_profiles(profiles, relaxed).count()
        if count:
            query = params.copy()
            query.pop(field, None)
            query.pop('page', None)
            suggestions.append({'field': field.replace('_', ' '), 'count': count, 'query': query.urlencode()})
    return sorted(suggestions, key=lambda row: (-row['count'], row['field']))[:3]
