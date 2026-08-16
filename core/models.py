from django.db import models
from django.utils import timezone
import fitz
# ==========================================
# 1. TABEL PERSONEL (Data Karyawan & Regu)
# ==========================================
class Personel(models.Model):
    REGU_CHOICES = [
        ('A', 'Regu A'),
        ('B', 'Regu B'),
        ('C', 'Regu C'),
        ('D', 'Regu D'),
        ('Non-Shift', 'Non-Shift'),
    ]
    
    nama = models.CharField(max_length=100)
    jabatan = models.CharField(max_length=100, blank=True, null=True)
    regu = models.CharField(max_length=15, choices=REGU_CHOICES, default='Non-Shift')

    def __str__(self):
        return f"{self.nama} ({self.regu})"

# ==========================================
# 2. TABEL ABSENSI (Pencatatan Kehadiran)
# ==========================================
class Absensi(models.Model):
    STATUS_CHOICES = [
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('Sakit', 'Sakit'),
        ('Cuti', 'Cuti'),
    ]
    SHIFT_CHOICES = [
        ('Pagi', 'Pagi'),
        ('Sore', 'Sore'),
        ('Malam', 'Malam'),
        ('Non-Shift', 'Non-Shift'),
    ]

    personel = models.ForeignKey(Personel, on_delete=models.CASCADE)
    tanggal = models.DateField(default=timezone.now)
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Hadir')
    keterangan = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.personel.nama} - {self.tanggal} ({self.status})"

# ==========================================
# 3. TABEL PEKERJAAN (Data SR, FLM, CM, PM)
# ==========================================
class Pekerjaan(models.Model):
    JENIS_CHOICES = [
        ('FLM', 'First Line Maintenance (FLM)'),
        ('CM', 'Corrective Maintenance (CM)'),
        ('PM', 'Preventive Maintenance (PM)'),
    ]
    
    AREA_CHOICES = [
        ('Boiler', 'Boiler'),
        ('Turbine', 'Turbine'),
        ('Coal Handling', 'Coal Handling'),
        ('Ash Handling', 'Ash Handling'),
        ('WTP', 'Water Treatment Plant (WTP)'),
        ('Elektrikal', 'Elektrikal'),
        ('Lainnya', 'Lainnya'),
    ]
    
    STATUS_CHOICES = [
        ('Open', 'Open / Belum Dikerjakan'),
        ('Progress', 'On Progress'),
        ('Finish', 'Selesai'),
    ]

    # Info Laporan
    judul_pekerjaan = models.CharField(max_length=200)
    jenis_pekerjaan = models.CharField(max_length=50, default='First Line Maintenance ( A )')
    area = models.CharField(max_length=30)
    deskripsi = models.TextField()
    
    # Waktu
    waktu_lapor = models.DateTimeField(default=timezone.now)
    waktu_selesai = models.DateTimeField(blank=True, null=True)
    
    # Status & Eksekutor
    status = models.CharField(max_length=20, default='Open')
    
    # Siapa yang mengerjakan? (Ini kunci untuk menghitung Scoreboard Personel/Regu)
    # Gunakan blank=True, null=True karena saat status "Open", belum tentu ada yang mengerjakan
    eksekutor = models.ForeignKey(Personel, on_delete=models.SET_NULL, blank=True, null=True, related_name='pekerjaan_diselesaikan')
    
    # Foto Evidence (Jika ingin ada fitur upload foto sebelum/sesudah)
    foto_evidence = models.ImageField(
        upload_to='evidence_pekerjaan/',
    	max_length=1000,
    	blank=True,
    	null=True
	)

    # Foto Evidence SESUDAH pekerjaan selesai
    foto_evidence_after = models.ImageField(
        upload_to='evidence_pekerjaan/',
        max_length=1000,
        blank=True,
        null=True
        )

    # Nama peralatan & nomor SR (untuk form input pekerjaan)
    nama_peralatan = models.CharField(max_length=200, blank=True, default='')
    nomor_sr = models.CharField(max_length=50, blank=True, default='')
    
    # Nama pelaksana (string original, mungkin multiple nama dipisah koma)
    nama_pelaksana = models.CharField(max_length=300, blank=True, default='')
    
    # User yang input (untuk role-based delete/update)
    created_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, blank=True, null=True, related_name="pekerjaan_dibuat")
    # M2M: semua personel yang ikut mengerjakan (untuk leaderboard fair)
    eksekutor_list = models.ManyToManyField(
        Personel, blank=True, related_name='pekerjaan_diikuti'
    )
    
    def __str__(self):
        return f"[{self.jenis_pekerjaan}] {self.judul_pekerjaan} - {self.status}"


# ==================== MODEL PTW (Permit To Work) ====================
class Ptw(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Finish', 'Finish'),
    ]
    
    nomor_ptw = models.CharField(max_length=100)
    no_wo = models.CharField(max_length=100, blank=True, default='')
    tanggal_terbit = models.DateField(default=timezone.now)
    nama_pekerjaan = models.TextField(blank=True, default='')
    area = models.CharField(max_length=100, blank=True, default='')
    peralatan = models.CharField(max_length=200, blank=True, default='')
    pelaksana = models.CharField(max_length=300, blank=True, default='')
    checklist = models.JSONField(default=list, blank=True)
    keterangan = models.TextField(blank=True, default='')
    bukti_isolasi = models.ImageField(
        upload_to='ptw/', max_length=1000, blank=True, null=True
    )
    bukti_release = models.ImageField(
        upload_to='ptw/', max_length=1000, blank=True, null=True
    )
    status = models.CharField(max_length=20, default='Open')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'core_ptw'
        ordering = ['-tanggal_terbit', '-id']
    
    def __str__(self):
        return f"PTW {self.nomor_ptw} - {self.status}"
# ==========================================
# 6. TABEL RTPM
# ==========================================

class RTPM(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Done', 'Done'),
        ('Overdue', 'Overdue'),
    ]

    equipment = models.CharField(max_length=200)
    deskripsi = models.TextField()
    area = models.CharField(max_length=100)
    tanggal = models.DateField()
    minggu_ke = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    pelaksana = models.CharField(max_length=100, blank=True, null=True)
    catatan = models.TextField(blank=True, null=True)

    # TAMBAHAN FOTO
    evidence = models.ImageField(
        upload_to='rtpm/',
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.equipment} - {self.tanggal}"


# ==================== MODEL USER PROFILE (Role-Based Access) ====================
class UserProfile(models.Model):
    REGU_CHOICES = [
        ('A', 'Produksi A'),
        ('B', 'Produksi B'),
        ('C', 'Produksi C'),
        ('D', 'Produksi D'),
    ]
    ROLE_CHOICES = [
        ('produksi', 'Produksi (A/B/C/D)'),
        ('rendal', 'Rendal'),
        ('har_listrik', 'Har Listrik'),
        ('har_mekanik', 'Har Mekanik'),
        ('har_konin', 'Har Konin'),
    ]
    user = models.OneToOneField(
        'auth.User', on_delete=models.CASCADE, related_name='profile'
    )
    regu = models.CharField(max_length=10, choices=REGU_CHOICES, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='produksi', blank=True, null=True)
    
    class Meta:
        db_table = 'core_userprofile'
    
    def __str__(self):
        return f"{self.user.username} - {self.regu or 'No Regu'}"


import fitz
import pytesseract

from pdf2image import convert_from_path


from django.db import models


class KnowledgeDocument(models.Model):

    CATEGORY_CHOICES = [
        ('SOP', 'SOP'),
        ('MANUAL', 'MANUAL'),
        ('HISTORY', 'HISTORY'),
    ]

    title = models.CharField(
        max_length=500
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    file = models.FileField(
        upload_to='knowledge/',
        max_length=1000
    )

    content = models.TextField(
        blank=True,
        null=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):

        # =========================
        # SAVE FILE FIRST
        # =========================
        super().save(*args, **kwargs)

        try:

            import fitz
            import pytesseract

            from pdf2image import convert_from_path

            full_text = ""

            # =========================
            # NORMAL PDF TEXT EXTRACTION
            # =========================
            pdf = fitz.open(self.file.path)

            for page in pdf:
                full_text += page.get_text()

            # =========================
            # OCR FALLBACK
            # FOR SCANNED PDF
            # =========================
            if len(full_text.strip()) < 50:

                print("OCR MODE:", self.title)

                images = convert_from_path(
                    self.file.path
                )

                ocr_text = ""

                for image in images:

                    ocr_text += pytesseract.image_to_string(
                        image,
                        lang='eng'
                    )

                full_text = ocr_text

            # =========================
            # LIMIT CONTENT SIZE
            # =========================
            full_text = full_text[:50000]

            # =========================
            # SAVE TO DATABASE
            # =========================
            KnowledgeDocument.objects.filter(
                id=self.id
            ).update(
                content=full_text
            )

            print("TEXT EXTRACTED:", self.title)

        except Exception as e:

            print("OCR ERROR:", self.title)
            print(str(e))


# ==================== MODEL AI RECOMMENDATION ====================
class AIRecommendation(models.Model):
    pekerjaan = models.OneToOneField(
        'Pekerjaan',
        on_delete=models.CASCADE,
        related_name='ai_recommendation'
    )
    query_text = models.TextField(blank=True, default='')
    similar_cases = models.JSONField(default=list)
    relevant_ikp = models.JSONField(default=list)
    # LLM Results
    kemungkinan_penyebab = models.JSONField(default=list)
    langkah_penanganan = models.JSONField(default=list)
    perhatian_keselamatan = models.JSONField(default=list)
    llm_model = models.CharField(max_length=100, blank=True, default='')
    generated_at = models.DateTimeField(default=timezone.now)
    is_ready = models.BooleanField(default=False)

    class Meta:
        db_table = 'core_ai_recommendation'

    def __str__(self):
        return f"AI Rec for CM-{self.pekerjaan_id}"
