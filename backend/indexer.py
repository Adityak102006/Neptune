"""
Image indexing and similarity search logic.
Scans directories for images, computes embeddings, and searches by cosine similarity.
"""

import os
import time
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .model import embedder

# Supported image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".tiff"}


class ImageIndex:
    """In-memory index of image embeddings for similarity search."""

    def __init__(self):
        self.embeddings: np.ndarray | None = None  # (N, 1280)
        self.image_paths: list[str] = []
        self.indexed_directory: str | None = None
        self.indexed_count: int = 0

    def scan_directory(self, directory: str) -> list[str]:
        """Recursively find all image files in the given directory."""
        image_files = []
        for root, _dirs, files in os.walk(directory):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    image_files.append(os.path.join(root, f))
        return sorted(image_files)

    def build_index(self, directory: str) -> dict:
        """
        Scan directory for images, compute embeddings, and store in memory.
        Returns status dict with count and timing info.
        """
        if not os.path.isdir(directory):
            raise ValueError(f"Directory not found: {directory}")

        image_files = self.scan_directory(directory)
        if not image_files:
            raise ValueError(f"No images found in: {directory}")

        start_time = time.time()
        embeddings_list = []
        valid_paths = []
        errors = []

        for path in image_files:
            try:
                emb = embedder.get_embedding(path)
                embeddings_list.append(emb)
                valid_paths.append(path)
            except Exception as e:
                errors.append({"path": path, "error": str(e)})

        if not embeddings_list:
            raise ValueError("Could not process any images from the directory.")

        stacked = np.array(embeddings_list)
        # Ensure embeddings are exactly 2D: (N, embedding_dim)
        self.embeddings = stacked.reshape(len(valid_paths), -1)
        self.image_paths = valid_paths
        self.indexed_directory = directory
        self.indexed_count = len(valid_paths)

        elapsed = time.time() - start_time

        return {
            "indexed_count": self.indexed_count,
            "directory": directory,
            "elapsed_seconds": round(elapsed, 2),
            "errors": errors[:10],  # Cap error reports
        }

    def search_similar(self, query_embedding: np.ndarray, top_k: int = 20) -> list[dict]:
        """
        Find top-k most similar images to the query embedding.
        Returns list of {path, filename, similarity} dicts.
        """
        if self.embeddings is None or len(self.image_paths) == 0:
            return []

        # Cosine similarity between query and all indexed embeddings
        query = query_embedding.reshape(1, -1)
        similarities = cosine_similarity(query, self.embeddings)[0]

        # Get top-k indices
        top_k = min(top_k, len(similarities))
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            path = self.image_paths[idx]
            results.append({
                "path": path,
                "filename": os.path.basename(path),
                "similarity": round(float(similarities[idx]) * 100, 1),
            })

        return results


# Singleton index
image_index = ImageIndex()
