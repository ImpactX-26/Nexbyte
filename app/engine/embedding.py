"""
NexByte MemoryShield - Embedding & Semantic Inconsistency Engine.
Computes semantic drift, cosine distance, and topical divergence against established reference memories.
"""

from typing import List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SemanticDriftEngine:
    """
    Evaluates semantic divergence between newly submitted memory inputs and
    previously established reference memory embeddings.
    """

    def __init__(self):
        # N-gram TF-IDF vectorizer provides fast, deterministic semantic representations
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
            max_features=5000
        )
        self.fitted = False
        # Fallback reference corpus representing standard safe conversational user memory topics
        self._default_safe_corpus = [
            "User prefers Python for data engineering and backend services",
            "User lives in Seattle and works remotely as a software engineer",
            "User's favorite color is navy blue and enjoys hiking on weekends",
            "User requested concise explanations with code examples in markdown",
            "User timezone is PST and working hours are 9 AM to 5 PM",
            "User likes high-level architectural summaries before deep code implementations"
        ]
        self._init_corpus()

    def _init_corpus(self):
        try:
            self.vectorizer.fit(self._default_safe_corpus)
            self.fitted = True
        except Exception:
            self.fitted = False

    def compute_drift(
        self,
        new_text: str,
        reference_memories: Optional[List[str]] = None
    ) -> Tuple[float, float, str]:
        """
        Calculates semantic drift score [0.0 - 1.0] and raw cosine similarity.
        Returns:
            drift_score: float (0.0 = aligned with baseline, 1.0 = heavy anomalous drift)
            max_similarity: float (0.0 = completely unrelated, 1.0 = identical)
            detail: str
        """
        if not new_text or not new_text.strip():
            return 0.5, 0.0, "Empty payload"

        corpus = reference_memories if reference_memories and len(reference_memories) > 0 else self._default_safe_corpus

        try:
            # Re-fit or transform
            combined = corpus + [new_text]
            tfidf_matrix = self.vectorizer.fit_transform(combined)

            ref_vectors = tfidf_matrix[:-1]
            new_vector = tfidf_matrix[-1:]

            similarities = cosine_similarity(new_vector, ref_vectors)[0]
            max_similarity = float(np.max(similarities)) if len(similarities) > 0 else 0.0
            avg_similarity = float(np.mean(similarities)) if len(similarities) > 0 else 0.0

            # If the user has a established profile, novel text that is 100% dissimilar (0.00 similarity)
            # and contains suspicious keywords will have drift.
            # Normal conversational memory has some natural topic shift (similarity ~ 0.15 - 0.40).
            # Extreme drift is when similarity is near 0.0 on an established profile or anomalous shifts happen.
            if len(corpus) <= 1:
                # Cold-start: baseline not yet established, low penalty
                drift_score = 0.10
                detail = "Cold-start memory cluster: baseline initialized"
            else:
                # Moderate drift scale
                drift_score = max(0.0, min(1.0, 1.0 - (max_similarity * 1.5)))
                detail = f"Max similarity to verified cluster: {max_similarity:.3f} (avg: {avg_similarity:.3f})"

            return float(drift_score), float(max_similarity), detail
        except Exception as e:
            return 0.20, 0.50, f"Drift computation fallback: {str(e)}"


semantic_engine = SemanticDriftEngine()
