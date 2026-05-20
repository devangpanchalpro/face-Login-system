"""
Custom template filters for face login dashboard.
"""
from django import template

register = template.Library()


@register.filter
def confidence_pct(distance):
    """
    Convert L2 distance to a human-readable percentage confidence score.
    L2 distance 0.0 = 100% match, 1.0 = 0% match.
    Formula: max(0, (1 - distance) * 100)
    """
    try:
        d = float(distance)
        pct = max(0.0, (1.0 - d) * 100.0)
        return f"{pct:.1f}%"
    except (ValueError, TypeError):
        return "N/A"
