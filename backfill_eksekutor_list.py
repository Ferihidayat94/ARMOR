import re
from django.db import connection, transaction
from core.models import Pekerjaan, Personel

print("Step 1: Build personel map & aliases...")
personel_map = {p.nama.upper(): p for p in Personel.objects.all()}
print(f"Total personel: {len(personel_map)}")

ALIASES = {
    # Regu A
    'AKBAR': 'AKBAR RULLA', 'SUNIR': 'SUNIR',
    'RENO': 'RENO FARLOVES', 'FARLOVES': 'RENO FARLOVES',
    'EKA': 'EKA CANDRA', 'CHANDRA': 'EKA CANDRA', 'CANDRA': 'EKA CANDRA',
    'AMINUDIN': 'AMINUDDIN', 'AMINUDDIN': 'AMINUDDIN',
    'HANAFI': 'HANAFI', 'HASAN': 'HASAN', 'DANDI': 'DANDI',
    'HENDRA': 'MUHAMMAD HENDRA', 'KAMIL': 'KAMIL',
    'MIDUN': 'SARMIDUN', 'SARMIDUN': 'SARMIDUN',
    'RAFI': 'RAFFY FERDINAN', 'RAFFI': 'RAFFY FERDINAN', 'RAFFY': 'RAFFY FERDINAN', 'FERDINAN': 'RAFFY FERDINAN',
    'DIKA': 'DIKA ARIA BARMA', 'BARMA': 'DIKA ARIA BARMA',
    'DEBBI': 'DEBIGUSTRARANDA', 'DEBI': 'DEBIGUSTRARANDA',
    'RANGGI': 'RANGGI', 'MAULID': 'MAULID', 'BUDI': 'BUDI',
    'GILANG': 'GILANG EN TAMAL', 'TAMAL': 'GILANG EN TAMAL',
    'SOLEH': 'MUHAMMAD SOLEH ALQODRI',
    'DIKI': 'DIKY APRIYANTO', 'DIKY': 'DIKY APRIYANTO', 'APRIYANTO': 'DIKY APRIYANTO',
    'WINNER': 'WINNER P T DASPIN SITANGGANG',
    'FERI': 'FERI HIDAYAT', 'HIDAYAT': 'FERI HIDAYAT',
    # Regu B
    'IWAN': 'IRWAN', 'IRWAN': 'IRWAN',
    'ABI': 'ABI WAHYUDI', 'ABY': 'ABI WAHYUDI', 'WAHYUDI': 'ABI WAHYUDI',
    'KEVIN': 'KEVIN ANANDA NURDIANSA',
    'YOGA': 'YOGA EKA PUTRA',
    'IRFAN': 'IRFAN SUSANTO',
    'SHIFA': 'SHIFA NUR HARYO', 'SIFA': 'SHIFA NUR HARYO',
    'IVAN': 'IVAN LESMANA', 'JASRIL': 'JASRIL RIZA',
    'NOVA': 'NOVA FEBRIAN', 'KHOIRUL': 'KHOIRUL', 'NOBI': 'NOBI',
    'YOGI': 'YOGI PRATAMA', 'GANDA': 'GANDA PUTRA SETIAWAN',
    'ICANDRA': 'ICANDRA', 'ICHANDRA': 'ICANDRA',
    'ZAMZAMI': 'ACHMAD ZAMZAMI', 'ZAMI': 'ACHMAD ZAMZAMI', 'SAMI': 'ACHMAD ZAMZAMI',
    'AMIN': 'MUHAMMAD AMIN', 'HABIBI': 'MUTTAQIN HABIBI',
    'VIRGI': 'VIRGIAWAN ERTANTO', 'VIRGIAWAN': 'VIRGIAWAN ERTANTO',
    'ODI': 'ODIDIO PRATAMA', 'ODIDIO': 'ODIDIO PRATAMA',
    # Regu C
    'WILLI': 'WILLY RISWENGKY', 'WILLY': 'WILLY RISWENGKY',
    'RIAN': 'M ADHZERIAN S R', 'RIYAN': 'M ADHZERIAN S R',
    'ROVEL': 'ROVEL POLVO', 'ADHA': 'ADHA', 'SALIM': 'SALIM',
    'DENIS': 'DENI SYAFUTRA', 'DENI': 'DENI SYAFUTRA',
    'ZAINUL': 'M ZAINUL ABDI', 'YAHYA': 'YAHYA',
    'EDWIN': 'EDWIN JASTIN', 'DARMAJI': 'DARMAJI', 'DARMAWAN': 'DARMAWAN',
    'FIDDIN': 'FIDDIN KISWANTO', 'FIDIN': 'FIDDIN KISWANTO',
    'AKHMAD': 'AKHMAD WISNU WARDANA', 'WISNU': 'AKHMAD WISNU WARDANA',
    'TRI': 'TRI SUHENDRI', 'IMAM': 'M IMAM SAPUTRO',
    'RIOS': 'REYVALDO RIOS', 'REYVALDO': 'REYVALDO RIOS',
    'RICO': 'RICO FERNANDO', 'RIKO': 'RICO FERNANDO',
    'INNAYA': 'INNAYA GALVANO', 'INAYA': 'INNAYA GALVANO',
    'ANDRI': 'ANDRI WIDIAN',
    # Regu D
    'NANANG': 'NANANG OKTAVIAN HIDAYAT',
    'LEO': 'LEO MALDINI', 'RINALDO': 'RINALDO',
    'ZULGHOFAH': 'M ZULGHOFAH', 'DECKY': 'DECKY PRADANA',
    'INDRA': 'INDRA ERYANSYAH', 'HORI': 'HORI',
    'KAMALUDIN': 'IMAM KAMALUDIN', 'IRFANI': 'MUHAMAD IRFANI',
    'MANSYUKUR': 'MANSYUKUR', 'TEGUH': 'TEGUH KARYA',
    'ZUBIR': 'ZUBIR', 'LEDIE': 'LEDIE AGUSSETIAWAN',
    'ABDI': 'ABDI SAPUTRA OCTAMAL',
    'SEPTIAN': 'RICO TRI SEPTIAN', 'SUBHANI': 'SUBHANI',
    'BERRY': 'BERRY GUSTIAWAN', 'YOPAN': 'YOPAN SANDRA WILLY',
    'RIDUWAN': 'MUHAMMAD RIDUWAN',
}

def parse_personels(raw_name):
    """Parsing string, return list of Personel objects yang match."""
    if not raw_name or raw_name.strip() == '':
        return []
    matched = []
    seen_ids = set()
    tokens = re.split(r',|\bDAN\b|\bdan\b|/|&|\+', raw_name)
    for token in tokens:
        token = token.strip().upper()
        token = re.sub(r'\([^)]*\)', '', token).strip()
        if not token:
            continue
        pers = None
        if token in personel_map:
            pers = personel_map[token]
        elif token in ALIASES:
            key = ALIASES[token].upper()
            if key in personel_map:
                pers = personel_map[key]
        else:
            for nama_upper, p in personel_map.items():
                if nama_upper.split()[0] == token:
                    pers = p
                    break
        if pers and pers.id not in seen_ids:
            matched.append(pers)
            seen_ids.add(pers.id)
    return matched

print("\nStep 2: Ambil semua data jobs dengan Nama Pelaksana...")
with connection.cursor() as c:
    c.execute("""
        SELECT "ID", "Nama Pelaksana"
        FROM jobs
        WHERE "Nama Pelaksana" IS NOT NULL AND "Nama Pelaksana" != ''
    """)
    rows = c.fetchall()
print(f"Total jobs dengan pelaksana: {len(rows)}")

print("\nStep 3: Mapping numeric_id → list personel...")
mapping = {}
for jid, pelaksana in rows:
    numeric_id = re.sub(r'[^0-9]', '', str(jid))
    if not numeric_id:
        continue
    personels = parse_personels(pelaksana)
    if personels:
        mapping[int(numeric_id)] = personels
print(f"Total mapping: {len(mapping)}")

print("\nStep 4: Populate eksekutor_list dan nama_pelaksana...")
print("(ini akan butuh beberapa menit untuk 5000+ records)")

updated_m2m = 0
updated_str = 0

# Build dict raw pelaksana untuk update nama_pelaksana string
raw_map = {}
for jid, pelaksana in rows:
    nid = re.sub(r'[^0-9]', '', str(jid))
    if nid:
        raw_map[int(nid)] = pelaksana[:300]  # truncate ke 300 char

with transaction.atomic():
    # Process in batches untuk speed
    pek_ids = list(mapping.keys())
    BATCH = 500
    for i in range(0, len(pek_ids), BATCH):
        batch_ids = pek_ids[i:i+BATCH]
        pekerjaan_qs = Pekerjaan.objects.filter(id__in=batch_ids)
        pek_by_id = {p.id: p for p in pekerjaan_qs}
        
        for pek_id in batch_ids:
            if pek_id not in pek_by_id:
                continue
            pek = pek_by_id[pek_id]
            personels = mapping[pek_id]
            
            # Set M2M
            pek.eksekutor_list.set(personels)
            updated_m2m += 1
            
            # Update nama_pelaksana string (kalau kosong)
            if not pek.nama_pelaksana and pek_id in raw_map:
                pek.nama_pelaksana = raw_map[pek_id]
                pek.save(update_fields=['nama_pelaksana'])
                updated_str += 1
        
        print(f"  Progress: {min(i+BATCH, len(pek_ids))}/{len(pek_ids)}")

print(f"\nDONE:")
print(f"  eksekutor_list ter-populate: {updated_m2m}")
print(f"  nama_pelaksana string ter-update: {updated_str}")

# Verifikasi
print("\nVERIFIKASI:")
with connection.cursor() as c:
    c.execute("""
        SELECT COUNT(DISTINCT cp.id)
        FROM core_pekerjaan cp
        JOIN core_pekerjaan_eksekutor_list cpel ON cp.id = cpel.pekerjaan_id
    """)
    print(f"  Pekerjaan dengan eksekutor_list: {c.fetchone()[0]}")
    
    c.execute("""
        SELECT pers.nama, pers.regu, COUNT(DISTINCT cpel.pekerjaan_id) AS jumlah
        FROM core_personel pers
        JOIN core_pekerjaan_eksekutor_list cpel ON pers.id = cpel.personel_id
        JOIN core_pekerjaan cp ON cpel.pekerjaan_id = cp.id
        WHERE cp.jenis_pekerjaan LIKE 'First Line Maintenance%'
        GROUP BY pers.nama, pers.regu
        ORDER BY jumlah DESC
        LIMIT 10
    """)
    print("\n  TOP 10 leaderboard (multi-personel counting):")
    for row in c.fetchall():
        print(f"    {row[0]:35s} {row[1]:12s} {row[2]:4d} SR")
