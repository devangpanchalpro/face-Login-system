"""
FAISS-based face search index for fast nearest-neighbor matching.
Supports 1000+ faces with millisecond search times.
"""
import faiss
import numpy as np
import pickle
from .models import FaceUser

DIMENSION = 128  # face_recognition always produces 128-d vectors


class FaceSearchIndex:
    """
    Builds a FAISS L2 index from all stored face encodings in the database.
    Provides fast nearest-neighbor search for face login matching.
    """

    def __init__(self):
        self.index = faiss.IndexFlatL2(DIMENSION)
        self.user_ids = []  # maps FAISS index position → FaceUser.id

    def build(self):
        """
        Load all face encodings from the database and build the FAISS index.
        Call this before performing any searches.
        """
        users = FaceUser.objects.all()
        if not users.exists():
            return

        vectors = []
        for user in users:
            enc = pickle.loads(user.face_encoding)
            vectors.append(enc)
            self.user_ids.append(user.id)

        matrix = np.array(vectors, dtype='float32')
        self.index.add(matrix)
        print(f"✅ FAISS index built with {len(self.user_ids)} users")

    def search(self, encoding, threshold=0.45):
        """
        Find the closest matching face in the index.

        Args:
            encoding: 128-d numpy array from face_recognition
            threshold: L2 distance threshold (lower = stricter)
                       0.4 = very strict, 0.5 = moderate, 0.6 = lenient

        Returns:
            (FaceUser, distance) if match found, (None, distance) otherwise
        """
        if self.index.ntotal == 0:
            return None, float('inf')

        query = np.array([encoding], dtype='float32')
        distances, indices = self.index.search(query, k=1)

        dist = float(distances[0][0])
        idx = int(indices[0][0])

        if dist < threshold and 0 <= idx < len(self.user_ids):
            user_id = self.user_ids[idx]
            try:
                user = FaceUser.objects.get(id=user_id)
                return user, dist
            except FaceUser.DoesNotExist:
                pass

        return None, dist
