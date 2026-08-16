"""
ARMOR AI - LLM Engine (Groq + Llama 3.1)
Generate langkah penanganan berdasarkan CM + IKP
"""
import os
import re
import logging

logger = logging.getLogger(__name__)

def get_groq_client():
    """Get Groq client dengan API key dari environment variable"""
    api_key = os.getenv('GROQ_API_KEY', '')
    
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan di environment")
    
    from groq import Groq
    return Groq(api_key=api_key)


def generate_handling_steps(cm_data, similar_cases, relevant_ikp):
    """
    Generate langkah penanganan menggunakan Groq/Llama.
    
    cm_data: dict dengan equipment, area, deskripsi
    similar_cases: list dari search_engine.find_similar_cm()
    relevant_ikp: list dari search_engine.find_relevant_ikp()
    
    Return: dict dengan langkah_penanganan, kemungkinan_penyebab, referensi
    """
    try:
        client = get_groq_client()
        
        # Susun context dari similar cases
        similar_text = ""
        if similar_cases:
            similar_text = "\n\nKASUS SERUPA DI HISTORIS:\n"
            for i, c in enumerate(similar_cases[:3], 1):
                similar_text += f"{i}. {('SR ' + c['nomor_sr'].strip()) if c.get('nomor_sr','').strip() and c.get('nomor_sr','').strip() != '-' else ('CM-' + str(c['cm_id']))} ({c['similarity']}% mirip)\n"
                similar_text += f"   Equipment: {c['nama_peralatan'] or '-'}\n"
                similar_text += f"   Area: {c['area'] or '-'}\n"
                similar_text += f"   Gejala: {c['deskripsi'][:150] if c['deskripsi'] else '-'}\n"
                similar_text += f"   Status: {c['status']}\n\n"
        
        # Susun context dari IKP
        ikp_text = ""
        if relevant_ikp:
            ikp_text = "\nINSTRUKSI KERJA RELEVAN:\n"
            for i, ikp in enumerate(relevant_ikp[:3], 1):
                ikp_text += f"{i}. {ikp['title']} ({ikp['relevance']}% relevan)\n"
                ikp_text += f"   Kategori: {ikp['category']}\n"
                ikp_text += f"   Isi: {ikp['chunk'][:300] if ikp['chunk'] else '-'}\n\n"
        
        # Buat prompt
        prompt = f"""Anda adalah AI Maintenance Assistant untuk PLTU Bangka. 
Berikan rekomendasi penanganan gangguan berdasarkan data berikut:

GANGGUAN SAAT INI:
- Equipment: {cm_data.get('nama_peralatan') or 'Tidak diketahui'}
- Area: {cm_data.get('area') or 'Tidak diketahui'}
- Deskripsi: {cm_data.get('deskripsi') or 'Tidak ada deskripsi'}
{similar_text}
{ikp_text}

Berikan response dalam format PERSIS seperti ini (dalam Bahasa Indonesia):

KEMUNGKINAN PENYEBAB:
1. [penyebab 1]
2. [penyebab 2]
3. [penyebab 3]

LANGKAH PENANGANAN:
1. [langkah 1]
2. [langkah 2]
3. [langkah 3]
4. [langkah 4]
5. [langkah 5]

PERHATIAN KESELAMATAN:
1. [hal yang perlu diperhatikan]
2. [hal yang perlu diperhatikan]

Jawab berdasarkan konteks PLTU dan data yang diberikan. Jika tidak ada data cukup, berikan rekomendasi umum yang sesuai."""

        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[
                {
                    'role': 'system',
                    'content': 'Anda adalah AI Maintenance Assistant ahli untuk PLTU (Pembangkit Listrik Tenaga Uap). Berikan rekomendasi teknis yang praktis dan terstruktur dalam Bahasa Indonesia.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        
        raw_text = response.choices[0].message.content
        
        # Parse response
        result = parse_llm_response(raw_text)
        result['raw'] = raw_text
        result['model'] = 'llama-3.1-8b-instant (Groq)'
        
        logger.info(f"LLM response generated: {len(raw_text)} chars")
        return result
        
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return {
            'error': str(e),
            'kemungkinan_penyebab': [],
            'langkah_penanganan': [],
            'perhatian_keselamatan': [],
            'raw': '',
            'model': 'error'
        }


def parse_llm_response(text):
    """Parse LLM response jadi structured dict."""
    result = {
        'kemungkinan_penyebab': [],
        'langkah_penanganan': [],
        'perhatian_keselamatan': [],
    }
    
    current_section = None
    
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Deteksi section header
        if 'KEMUNGKINAN PENYEBAB' in line.upper():
            current_section = 'kemungkinan_penyebab'
            continue
        elif 'LANGKAH PENANGANAN' in line.upper():
            current_section = 'langkah_penanganan'
            continue
        elif 'PERHATIAN KESELAMATAN' in line.upper():
            current_section = 'perhatian_keselamatan'
            continue
        
        # Tambah item ke section aktif
        if current_section and re.match(r'^\d+\.', line):
            item = re.sub(r'^\d+\.\s*', '', line).strip()
            if item and len(item) > 3:
                result[current_section].append(item)
    
    return result
