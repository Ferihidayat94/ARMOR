"""
Cron script: scan core_pekerjaan dengan eksekutor_id NULL,
apply smart matching, populate eksekutor + eksekutor_list M2M.
Run setiap 5 menit via cron.
"""
import re
from django.db import transaction
from core.models import Pekerjaan, Personel

personel_map = {p.nama.upper(): p for p in Personel.objects.all()}

ALIASES = {
    "AKBAR": "AKBAR RULLA", "SUNIR": "SUNIR",
    "RENO": "RENO FARLOVES", "FARLOVES": "RENO FARLOVES",
    "EKA": "EKA CANDRA", "CHANDRA": "EKA CANDRA", "CANDRA": "EKA CANDRA",
    "AMINUDIN": "AMINUDDIN", "AMINUDDIN": "AMINUDDIN",
    "HANAFI": "HANAFI", "HASAN": "HASAN", "DANDI": "DANDI",
    "HENDRA": "MUHAMMAD HENDRA", "KAMIL": "KAMIL",
    "MIDUN": "SARMIDUN", "SARMIDUN": "SARMIDUN",
    "RAFI": "RAFFY FERDINAN", "RAFFI": "RAFFY FERDINAN", "RAFFY": "RAFFY FERDINAN",
    "DIKA": "DIKA ARIA BARMA", "BARMA": "DIKA ARIA BARMA",
    "DEBBI": "DEBIGUSTRARANDA", "DEBI": "DEBIGUSTRARANDA", "DEBBY": "DEBIGUSTRARANDA",
    "RANGGI": "RANGGI", "MAULID": "MAULID", "BUDI": "BUDI",
    "GILANG": "GILANG EN TAMAL", "TAMAL": "GILANG EN TAMAL",
    "SOLEH": "MUHAMMAD SOLEH ALQODRI",
    "DIKI": "DIKY APRIYANTO", "DIKY": "DIKY APRIYANTO", "APRIYANTO": "DIKY APRIYANTO",
    "WINNER": "WINNER P T DASPIN SITANGGANG",
    "FERI": "FERI HIDAYAT", "HIDAYAT": "FERI HIDAYAT",
    "IWAN": "IRWAN", "IRWAN": "IRWAN",
    "ABI": "ABI WAHYUDI", "ABY": "ABI WAHYUDI", "WAHYUDI": "ABI WAHYUDI",
    "KEVIN": "KEVIN ANANDA NURDIANSA",
    "YOGA": "YOGA EKA PUTRA",
    "IRFAN": "IRFAN SUSANTO",
    "SHIFA": "SHIFA NUR HARYO", "SIFA": "SHIFA NUR HARYO",
    "IVAN": "IVAN LESMANA", "JASRIL": "JASRIL RIZA",
    "NOVA": "NOVA FEBRIAN", "KHOIRUL": "KHOIRUL", "NOBI": "NOBI",
    "YOGI": "YOGI PRATAMA", "GANDA": "GANDA PUTRA SETIAWAN",
    "ICANDRA": "ICANDRA", "ICHANDRA": "ICANDRA",
    "ZAMZAMI": "ACHMAD ZAMZAMI", "ZAMI": "ACHMAD ZAMZAMI", "SAMI": "ACHMAD ZAMZAMI",
    "AMIN": "MUHAMMAD AMIN", "HABIBI": "MUTTAQIN HABIBI", "MUTTAQIN": "MUTTAQIN HABIBI",
    "VIRGI": "VIRGIAWAN ERTANTO", "VIRGIAWAN": "VIRGIAWAN ERTANTO",
    "ODI": "ODIDIO PRATAMA", "ODIDIO": "ODIDIO PRATAMA",
    "WILLI": "WILLY RISWENGKY", "WILLY": "WILLY RISWENGKY",
    "RIAN": "M ADHZERIAN S R", "RIYAN": "M ADHZERIAN S R", "ADHZERIAN": "M ADHZERIAN S R",
    "ROVEL": "ROVEL POLVO", "ADHA": "ADHA", "SALIM": "SALIM",
    "DENIS": "DENI SYAFUTRA", "DENI": "DENI SYAFUTRA",
    "ZAINUL": "M ZAINUL ABDI", "YAHYA": "YAHYA",
    "EDWIN": "EDWIN JASTIN", "JASTIN": "EDWIN JASTIN",
    "DARMAJI": "DARMAJI", "DARMAWAN": "DARMAWAN",
    "FIDDIN": "FIDDIN KISWANTO", "FIDIN": "FIDDIN KISWANTO",
    "AKHMAD": "AKHMAD WISNU WARDANA", "WISNU": "AKHMAD WISNU WARDANA",
    "TRI": "TRI SUHENDRI", "SUHENDRI": "TRI SUHENDRI",
    "IMAM": "M IMAM SAPUTRO", "SAPUTRO": "M IMAM SAPUTRO",
    "REYVALDO": "REYVALDO RIOS", "RIOS": "REYVALDO RIOS",
    "RICO": "RICO FERNANDO", "RIKO": "RICO FERNANDO",
    "INNAYA": "INNAYA GALVANO", "INAYA": "INNAYA GALVANO",
    "ANDRI": "ANDRI WIDIAN",
    "NANANG": "NANANG OKTAVIAN HIDAYAT",
    "LEO": "LEO MALDINI", "RINALDO": "RINALDO",
    "ZULGHOFAH": "M ZULGHOFAH", "DECKY": "DECKY PRADANA",
    "INDRA": "INDRA ERYANSYAH", "HORI": "HORI",
    "KAMALUDIN": "IMAM KAMALUDIN", "IRFANI": "MUHAMAD IRFANI",
    "MANSYUKUR": "MANSYUKUR", "TEGUH": "TEGUH KARYA",
    "ZUBIR": "ZUBIR", "LEDIE": "LEDIE AGUSSETIAWAN",
    "ABDI": "ABDI SAPUTRA OCTAMAL",
    "SEPTIAN": "RICO TRI SEPTIAN", "SUBHANI": "SUBHANI",
    "BERRY": "BERRY GUSTIAWAN", "YOPAN": "YOPAN SANDRA WILLY",
    "RIDUWAN": "MUHAMMAD RIDUWAN",
}

def parse_personels(raw_name):
    if not raw_name or raw_name.strip() == "":
        return []
    matched = []
    seen_ids = set()
    tokens = re.split(r",|DAN|dan|/|&|\+", raw_name)
    for token in tokens:
        token = token.strip().upper()
        token = re.sub(r"\([^)]*\)", "", token).strip()
        if not token:
            continue
        pers = None
        # 1. Exact match dengan personel
        if token in personel_map:
            pers = personel_map[token]
        # 2. Exact match dengan alias
        elif token in ALIASES:
            key = ALIASES[token].upper()
            if key in personel_map:
                pers = personel_map[key]
        else:
            # 3. Bandingkan first word token dengan first word personel
            #    (untuk "EKA CHANDRA" match "EKA CANDRA")
            token_first = token.split()[0] if token else ""
            if token_first in personel_map:
                pers = personel_map[token_first]
            elif token_first in ALIASES:
                key = ALIASES[token_first].upper()
                if key in personel_map:
                    pers = personel_map[key]
            else:
                for nama_upper, p in personel_map.items():
                    if nama_upper.split()[0] == token_first:
                        pers = p
                        break
        if pers and pers.id not in seen_ids:
            matched.append(pers)
            seen_ids.add(pers.id)
    return matched

# Scan: eksekutor=NULL DAN punya nama_pelaksana
to_process = Pekerjaan.objects.filter(
    eksekutor__isnull=True
).exclude(nama_pelaksana="").exclude(nama_pelaksana__isnull=True)

total = to_process.count()
matched_count = 0

with transaction.atomic():
    for pek in to_process:
        personels = parse_personels(pek.nama_pelaksana)
        if personels:
            pek.eksekutor = personels[0]
            pek.save(update_fields=["eksekutor"])
            pek.eksekutor_list.set(personels)
            matched_count += 1

print(f"[CRON {total} scanned, {matched_count} matched]")
