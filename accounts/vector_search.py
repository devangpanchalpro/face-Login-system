"""
pgvector-based face search — replaces FAISS.
Uses PostgreSQL's native vector similarity search with HNSW indexing
for millisecond-level nearest-neighbor matching on millions of faces.
"""
# pyrefly: ignore [missing-import]
from pgvector.django import L2Distance
from .models import FaceEncoding


def search_face(encoding, threshold=0.55, limit=5):
    """
    Find the closest matching face using pgvector L2 distance.

    This runs entirely inside PostgreSQL using the HNSW index,
    so it scales to millions of faces with sub-10ms search times.

    Args:
        encoding: 128-d numpy array from face_recognition
        threshold: L2 distance threshold (lower = stricter match)
                   0.40 = very strict, 0.55 = strict, 0.70 = moderate
                   Note: This is L2 distance (not squared, unlike FAISS)
        limit: Maximum number of candidates to return

    Returns:
        (FaceUser, distance) if match found, (None, distance) otherwise
    """
    query_vector = encoding.tolist()

    # Check if any encodings exist
    if not FaceEncoding.objects.exists():
        return None, float('inf')

    # Search for nearest neighbors using pgvector HNSW index
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
