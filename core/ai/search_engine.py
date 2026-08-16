"""
ARMOR AI - Search Engine
Cari similar CM + relevant IKP berdasarkan query CM baru
"""
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

import os as _os; _BASE = _os.path.dirname(_os.path.abspath(__file__)); CM_CACHE = _os.path.join(_BASE, 'cm_vectors.pkl')
IKP_CACHE = _os.path.join(_BASE, 'ikp_vectors.pkl')

_cm_index = None
_ikp_index = None


def load_indexes():
    """Load CM dan IKP indexes dari cache."""
    global _cm_index, _ikp_index
    from core.ai.embeddings import load_cache
    
    if _cm_index is None:
        _cm_index = load_cache(CM_CACHE)
        if _cm_index:
            logger.info(f"CM index loaded: {len(_cm_index['ids'])} records")
        else:
            logger.warning("CM index not found — run build_cm_index() first")
    
    if _ikp_index is None:
        _ikp_index = load_cache(IKP_CACHE)
        if _ikp_index:
            logger.info(f"IKP index loaded: {len(_ikp_index['chunks'])} chunks")
        else:
            logger.warning("IKP index not found — run build_ikp_index() first")


def find_similar_cm(query_text, top_k=5, exclude_id=None):
    """
    Cari CM historis yang mirip dengan query.
    Return: list of dicts dengan similarity score
    """
    load_indexes()
    
    if not _cm_index:
        return []
    
    from core.ai.embeddings import embed_text, cosine_similarity_scores
    
    query_vec = embed_text(query_text)
    vectors = np.array(_cm_index['vectors'])
    scores = cosine_similarity_scores(query_vec, vectors)
    
    # Sort by score descending
    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True
    )
    
    results = []
    for idx, score in ranked:
        if score < 0.3:  # Minimum similarity threshold
            continue
        
        meta = _cm_index['metadata'][idx]
        cm_id = meta['id']
        
        # Skip kalau ID sama (exclude self)
        if exclude_id and cm_id == exclude_id:
            continue
        
        results.append({
            'cm_id': cm_id,
            'similarity': round(float(score) * 100, 1),
            'nama_peralatan': meta.get('nama_peralatan') or '-',
            'area': meta.get('area') or '-',
            'deskripsi': (meta.get('deskripsi') or '')[:200],
            'status': meta.get('status') or '-',
            'waktu_lapor': str(meta.get('waktu_lapor') or '-'),
        })
        
        if len(results) >= top_k:
            break
    
    return results


def find_relevant_ikp(query_text, top_k=3):
    """
    Cari chunk IKP yang relevan dengan query.
    Return: list of dicts dengan relevance score
    """
    load_indexes()
    
    if not _ikp_index:
        return []
    
    from core.ai.embeddings import embed_text, cosine_similarity_scores
    
    query_vec = embed_text(query_text)
    vectors = np.array(_ikp_index['vectors'])
    scores = cosine_similarity_scores(query_vec, vectors)
    
    # Sort by score descending
    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True
    )
    
    results = []
    seen_docs = set()  # Hindari duplicate dari dokumen yang sama
    
    for idx, score in ranked:
        if score < 0.25:  # Threshold lebih rendah untuk IKP
            continue
        
        meta = _ikp_index['metadata'][idx]
        doc_id = meta['doc_id']
        
        # Ambil max 1 chunk per dokumen (avoid flooding dari 1 IKP)
        if doc_id in seen_docs:
            continue
        seen_docs.add(doc_id)
        
        results.append({
            'doc_id': doc_id,
            'title': meta.get('title') or '-',
            'category': meta.get('category') or '-',
            'relevance': round(float(score) * 100, 1),
            'chunk': _ikp_index['chunks'][idx][:300],
        })
        
        if len(results) >= top_k:
            break
    
    return results


def get_ai_recommendation(cm_id):
    """
    Main function: get AI recommendation untuk 1 CM.
    Return: dict dengan similar_cases + relevant_ikp
    """
    from core.models import Pekerjaan
    
    try:
        cm = Pekerjaan.objects.get(id=cm_id)
    except Pekerjaan.DoesNotExist:
        logger.error(f"CM id={cm_id} not found")
        return None
    
    # Buat query text dari CM
    query = f"{cm.nama_peralatan or ''} {cm.area or ''} {cm.deskripsi or ''}"
    query = query.strip()
    
    if not query:
        logger.warning(f"CM id={cm_id} has no searchable text")
        return None
    
    logger.info(f"Getting recommendation for CM-{cm_id}: {query[:80]}...")
    
    similar_cms = find_similar_cm(query, top_k=5, exclude_id=cm_id)
    relevant_ikp = find_relevant_ikp(query, top_k=3)
    
    # Generate langkah penanganan via LLM (Groq)
    cm_data = {
        'nama_peralatan': cm.nama_peralatan or '',
        'area': cm.area or '',
        'deskripsi': cm.deskripsi or '',
    }
    
    handling = {}
    try:
        from core.ai.llm_engine import generate_handling_steps
        handling = generate_handling_steps(cm_data, similar_cms, relevant_ikp)
        logger.info(f"CM-{cm_id}: LLM generated {len(handling.get('langkah_penanganan', []))} steps")
    except Exception as e:
        logger.error(f"LLM error for CM-{cm_id}: {e}")

    result = {
        'cm_id': cm_id,
        'query': query[:200],
        'similar_cases': similar_cms,
        'relevant_ikp': relevant_ikp,
        'total_similar': len(similar_cms),
        'total_ikp': len(relevant_ikp),
        # LLM Result
        'kemungkinan_penyebab': handling.get('kemungkinan_penyebab', []),
        'langkah_penanganan': handling.get('langkah_penanganan', []),
        'perhatian_keselamatan': handling.get('perhatian_keselamatan', []),
        'llm_model': handling.get('model', ''),
    }
    
    logger.info(
        f"CM-{cm_id}: {len(similar_cms)} similar cases, "
        f"{len(relevant_ikp)} relevant IKP, "
        f"{len(handling.get('langkah_penanganan',[]))} handling steps"
    )
    
    return result
