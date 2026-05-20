"""
Custom template filters for face login dashboard.
"""
from django import template

register = template.Library()


@register.filter
def confidence_pct(distance):
    """
    Convert L2 distance to a human-readable percentage confidence score.

    For InsightFace normalized 512-d embeddings:
        L2 distance 0.0 = identical faces (100% match)
        L2 distance ~1.414 = completely different (0% match)

    Formula: max(0, (1 - (distance / 1.414)) * 100)
    This maps the full L2 range [0, sqrt(2)] to [100%, 0%].
    """
    try:
        d = float(distance)
        # sqrt(2) ≈ 1.414 is the max L2 distance for normalized vectors
        pct = max(0.0, (1.0 - d / 1.414) * 100.0)
        return f"{pct:.1f}%"
    except (ValueError, TypeError):
        return "N/A"
