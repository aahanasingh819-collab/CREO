"""Transparent deterministic scoring. No legal certification, price guesses, or embeddings."""
import re
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone


def words(value):
    return set(re.findall(r'\w+', value.casefold()))


def commercial_warnings(brief, profile, items):
    warnings = []
    if profile.is_demo or any(item.is_demo for item in items):
        warnings.append('Fictional demo work is not evidence of commercial readiness or production capability.')
    if brief and brief.commercial_use:
        if not items:
            warnings.append('No portfolio entries are available to review for source and usage information.')
        missing = sum(not item.licensing_notes.strip() for item in items)
        if missing:
            warnings.append(f'{missing} portfolio project(s) have no source or usage notes. Request those details.')
        restrictions = ('non-commercial', 'noncommercial', 'personal use only', 'editorial use only', 'not for commercial', 'research only')
        flagged = [item.title for item in items if any(term in item.licensing_notes.casefold() for term in restrictions)]
        if flagged:
            warnings.append('Usage restriction language appears in: ' + ', '.join(flagged) + '. Review the original terms with the creator.')
        if any(item.video_url for item in items):
            warnings.append('A hosted video link does not establish rights to footage, music, likenesses, or source assets.')
        warnings.append('Confirm model/tool terms for the actual plan and version, source licenses, and any required releases for your intended use.')
    warnings.append('All usage information is self-reported. No automated check can establish legal clearance.')
    return warnings


def score_creator(brief, profile, requirements=None):
    items = list(profile.portfolio_items.all())
    requirements = requirements or {name: list(getattr(brief, name).all()) for name in ['skills', 'tools', 'specializations']}
    rows = []

    def row(label, weight, fraction, reason):
        rows.append({'label': label, 'weight': weight, 'earned': round(weight * fraction, 2), 'reason': reason})

    formats = [i for i in items if i.format == brief.content_type]
    row('Content type', 25, bool(formats), f'{len(formats)} portfolio entry/entries list {brief.get_content_type_display()}; metadata is creator-supplied.')
    aspect = [i for i in formats if i.aspect_ratio == brief.aspect_ratio]
    row('Aspect ratio', 10, bool(aspect), f'{len(aspect)} entry/entries combine the requested content type and {brief.aspect_ratio}.')
    requested_words = words(brief.style)
    style_match = max((len(words(i.style) & requested_words) / len(requested_words) for i in formats), default=0) if requested_words else 0
    row('Visual style', 15, style_match, 'Word overlap with the style of the best portfolio entry in the requested content type; not visual analysis.')
    if requirements['tools']:
        listed = {t.pk for t in profile.tools.all()}
        in_work = {t.pk for item in items for t in item.tools.all()}
        names_work = [t.name for t in requirements['tools'] if t.pk in in_work]
        names_claim = [t.name for t in requirements['tools'] if t.pk in listed and t.pk not in in_work]
        fraction = (len(names_work) + .5 * len(names_claim)) / len(requirements['tools'])
        row('Tools', 20, fraction, f'Portfolio-listed: {", ".join(names_work) or "none"}. Profile-only (half credit): {", ".join(names_claim) or "none"}.')
    for field, label, weight in [('skills', 'Skills', 15), ('specializations', 'Specializations', 10)]:
        if requirements[field]:
            listed = {v.pk for v in getattr(profile, field).all()}
            matched = [v.name for v in requirements[field] if v.pk in listed]
            row(label, weight, len(matched) / len(requirements[field]), f'Self-declared matches: {", ".join(matched) or "none"}.')
    row('Availability', 5, {'AVAILABLE': 1, 'LIMITED': .5, 'UNAVAILABLE': 0}.get(profile.availability, 0),
        profile.get_availability_display() + '; deadline commitment must be confirmed directly.')
    total = sum(r['weight'] for r in rows)
    score = int((Decimal(str(sum(r['earned'] for r in rows))) * 100 / total).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    warnings = commercial_warnings(brief, profile, items)
    if brief.deadline < timezone.localdate():
        warnings.insert(0, 'This brief’s deadline has passed. Update it before evaluating availability.')
    return {'profile': profile, 'score': score, 'rows': rows, 'weight_total': total, 'warnings': warnings,
            'items': items, 'demo': profile.is_demo or any(i.is_demo for i in items)}


def rank_creators(brief, profiles):
    requirements = {name: list(getattr(brief, name).all()) for name in ['skills', 'tools', 'specializations']}
    return sorted((score_creator(brief, p, requirements) for p in profiles), key=lambda match: (-match['score'], match['profile'].display_name.casefold(), match['profile'].pk))
