"""
ARMOR AI - Embedding Engine
Pakai sentence-transformers all-MiniLM-L6-v2 (gratis, lokal)
"""
import numpy as np
import pickle
import os
import logging

logger = logging.getLogger(__name__)

MODEL_NAME = '/app/models/paraphrase-multilingual-mpnet-base-v2'
import os as _os
_BASE = _os.path.dirname(_os.path.abspath(__file__))
CM_CACHE_PATH = _os.path.join(_BASE, 'cm_vectors.pkl')
IKP_CACHE_PATH = _os.path.join(_BASE, 'ikp_vectors.pkl')
CACHE_PATH = CM_CACHE_PATH  # backward compat

_model = None
_cache = {}

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers model...")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded.")
    return _model

def embed_text(text):
    """Convert text to vector embedding."""
    if not text or not text.strip():
        return np.zeros(384)
    model = get_model()
    return model.encode(str(text).strip(), normalize_embeddings=True)

def embed_batch(texts):
    """Convert list of texts to vectors (faster than one by one)."""
    model = get_model()
    clean = [str(t).strip() if t else '' for t in texts]
    return model.encode(clean, normalize_embeddings=True, show_progress_bar=True)

def cosine_similarity_scores(query_vec, corpus_vecs):
    """Calculate cosine similarity antara 1 query dan banyak corpus."""
    from sklearn.metrics.pairwise import cosine_similarity
    q = query_vec.reshape(1, -1)
    scores = cosine_similarity(q, corpus_vecs)[0]
    return scores

def save_cache(data, path=CACHE_PATH):
    """Simpan vector cache ke disk."""
    with open(path, 'wb') as f:
        pickle.dump(data, f)
    logger.info(f"Cache saved: {path}")

def load_cache(path=CACHE_PATH):
    """Load vector cache dari disk."""
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
    return None
