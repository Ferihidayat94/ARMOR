"""
ARMOR AI - Indexer
Index historis CM + PDF IKP ke vector store
"""
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

def build_cm_index():
    """
    Index semua CM Corrective ke vector store.
    Return: dict dengan vectors, ids, texts
    """
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'armor_site.settings')
    
    from core.models import Pekerjaan
    from core.ai.embeddings import embed_batch, save_cache, load_cache
    
    logger.info("Building CM index...")
    
    # Ambil semua CM
    cms = Pekerjaan.objects.filter(
        jenis_pekerjaan__icontains='Corrective'
    ).values('id', 'nomor_sr', 'nama_peralatan', 'area', 'deskripsi', 'status', 'waktu_lapor')
    
    cm_list = list(cms)
    if not cm_list:
        logger.warning("No CM data found!")
        return None
    
    # Buat text representasi untuk setiap CM
    texts = []
    for cm in cm_list:
        text = f"{cm.get('nama_peralatan','') or ''} {cm.get('area','') or ''} {cm.get('deskripsi','') or ''}"
        texts.append(text.strip())
    
    logger.info(f"Embedding {len(texts)} CM records...")
    vectors = embed_batch(texts)
    
    # Simpan ke cache
    cache_data = {
        'type': 'cm',
        'ids': [cm['id'] for cm in cm_list],
        'texts': texts,
        'metadata': cm_list,
        'vectors': vectors,
    }
    save_cache(cache_data, '/app/core/ai/cm_vectors.pkl')
    logger.info(f"CM index built: {len(texts)} records")
    return cache_data


def build_ikp_index():
    """
    Index semua PDF IKP ke vector store (per chunk 500 chars).
    Return: dict dengan vectors, chunks, metadata
    """
    from core.models import KnowledgeDocument
    from core.ai.embeddings import embed_batch, save_cache
    from core.ai.pdf_parser import extract_text_from_pdf
    
    logger.info("Building IKP index...")
    
    docs = KnowledgeDocument.objects.all()
    
    all_chunks = []
    all_metadata = []
    
    for doc in docs:
        try:
            file_path = doc.file.path
            text = extract_text_from_pdf(file_path)
            if not text or len(text.strip()) < 50:
                logger.warning(f"SKIP (empty): {doc.title}")
                continue
            
            # Chunk text per 500 chars dengan overlap 100
            chunks = chunk_text(text, chunk_size=500, overlap=100)
            
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadata.append({
                    'doc_id': doc.id,
                    'title': doc.title,
                    'category': doc.category,
                    'chunk_idx': i,
                    'total_chunks': len(chunks),
                })
            
            logger.info(f"Indexed: {doc.title} ({len(chunks)} chunks)")
        except Exception as e:
            logger.error(f"Error indexing {doc.title}: {e}")
            continue
    
    if not all_chunks:
        logger.warning("No IKP chunks to index!")
        return None
    
    logger.info(f"Embedding {len(all_chunks)} IKP chunks...")
    vectors = embed_batch(all_chunks)
    
    cache_data = {
        'type': 'ikp',
        'chunks': all_chunks,
        'metadata': all_metadata,
        'vectors': vectors,
    }
    save_cache(cache_data, '/app/core/ai/ikp_vectors.pkl')
    logger.info(f"IKP index built: {len(all_chunks)} chunks from {docs.count()} docs")
    return cache_data


def chunk_text(text, chunk_size=500, overlap=100):
    """Split text menjadi chunks dengan overlap."""
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    
    return chunks
