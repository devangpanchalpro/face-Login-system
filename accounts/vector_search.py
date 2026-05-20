"""
pgvector-based face search — optimized for InsightFace ArcFace embeddings.
Uses PostgreSQL's native vector similarity search with HNSW indexing
for millisecond-level nearest-neighbor matching on millions of faces.

Note: InsightFace returns L2-normalized embeddings, so L2 distance
between two normalized vectors relates to cosine similarity as:
    L2_dist = sqrt(2 - 2*cos_sim)
    cos_sim=1.0 (identical) → L2=0.0
    cos_sim=0.5 → L2≈1.0
    cos_sim=0.0 → L2≈1.414

For normalized 512-d ArcFace embeddings:
    L2 < 0.8  = strong match
    L2 < 1.0  = moderate match
    L2 < 1.2  = weak match
"""
# pyrefly: ignore [missing-import]
from pgvector.django import L2Distance
from django.db import connection
from .models import FaceEncoding


def search_face(encoding, threshold=0.9, limit=1):
    """
    Find the closest matching face using pgvector L2 distance.

    This runs entirely inside PostgreSQL using the HNSW index,
    so it scales to millions of faces with sub-10ms search times.

    Args:
        encoding: 512-d numpy array from InsightFace (L2-normalized)
        threshold: L2 distance threshold (lower = stricter match)
                   0.8 = very strict, 0.9 = strict, 1.0 = moderate
        limit: Maximum number of candidates to return

    Returns:
        (FaceUser, distance) if match found, (None, distance) otherwise
    """
    query_vector = encoding.tolist()

    # Check if any encodings exist
    if not FaceEncoding.objects.exists():
        return None, float('inf')

    # Set HNSW search quality for this query (higher = more accurate, slightly slower)
    # ef_search=100 is optimal for 5M+ vectors — gives >99% recall
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL hnsw.ef_search = 100")

    # Search for nearest neighbor using pgvector HNSW index
    results = FaceEncoding.objects.annotate(
        distance=L2Distance('encoding', query_vector)
    ).select_related('user').order_by('distance')[:limit]

    results = list(results)

    if not results:
        return None, float('inf')

    best = results[0]
    best_distance = float(best.distance)

    if best_distance < threshold:
        return best.user, best_distance

    # No match under threshold — return closest distance for debugging
    return None, best_distance
