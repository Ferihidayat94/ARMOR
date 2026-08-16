from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from core.views import knowledge_search
from core.views import ai_recommendation_detail
# ================= IMPORT SEMUA VIEW YANG DIBUTUHKAN =================
from core.views import (
    # --- RTPM ---
    rtpm_dashboard,
    rtpm_tambah_jadwal,
    rtpm_hapus_jadwal,
    rtpm_input_pelaksanaan,
    rtpm_edit_pelaksanaan,
    rtpm_export_excel,
    rtpm_export_pdf,            # <-- export PDF RTPM

    # --- MONITORING PEKERJAAN (JOBS) ---
    input_pekerjaan,
    daftar_pekerjaan,
    dashboard_utama,
    hapus_pekerjaan,
    edit_nomor_sr,
    export_pekerjaan,
    update_pekerjaan,

    # --- PTW ---
    ptw_list,
    ptw_tambah,
    ptw_hapus,
    ptw_selesai,
    ptw_export_excel,           # <-- export Excel PTW
    ptw_export_pdf,             # <-- export PDF PTW


)

# ================= RUTE URL =================
urlpatterns = [
    path('admin/', admin.site.urls),

    # ROOT REDIRECT
    path('', lambda request: redirect('login/'), name='root_redirect'),

    # AUTHENTICATION
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    
    # GANTI PASSWORD
    # === GANTI PASSWORD DISABLED — hanya admin via server ===
    # path('ganti-password/', auth_views.PasswordChangeView.as_view(
    #     template_name='registration/password_change_form.html',
    #     success_url='/ganti-password/sukses/'
    # ), name='password_change'),
    # path('ganti-password/sukses/', auth_views.PasswordChangeDoneView.as_view(
    #     template_name='registration/password_change_done.html'
    # ), name='password_change_done'),

    # DASHBOARD
    path('dashboard/', dashboard_utama, name='dashboard'),
    
    # AI RECOMMENDATION API
    path('api/ai-recommendation/<int:cm_id>/', ai_recommendation_detail, name='ai_recommendation_detail'),

    # ========== ABSENSI (DINONAKTIFKAN) ==========
    # path('absensi-personel/', halaman_input, name='halaman_input'),
    # path('daftar/', daftar_personel, name='daftar'),
    # path('hapus/<int:id>/', hapus_personel, name='hapus'),
    # path('export/', export_excel, name='export'),
    # ============================================

    # PEKERJAAN (JOBS)
    path('edit-nomor-sr/<str:id>/', edit_nomor_sr, name='edit_nomor_sr'),
    path('hapus-pekerjaan/<str:id>/', hapus_pekerjaan, name='hapus_pekerjaan'),
    path('export-pekerjaan/', export_pekerjaan, name='export_pekerjaan'),
    path('input-pekerjaan/', input_pekerjaan, name='input_pekerjaan'),
    path('daftar-pekerjaan/', daftar_pekerjaan, name='daftar_pekerjaan'),
    path('update-pekerjaan/<str:id>/', update_pekerjaan, name='update_pekerjaan'),

    # PERMIT TO WORK (PTW)
    path('ptw/', ptw_list, name='ptw_list'),
    path('ptw/tambah/', ptw_tambah, name='ptw_tambah'),
    path('ptw/hapus/<int:id>/', ptw_hapus, name='ptw_hapus'),
    path('ptw/selesai/<int:id>/', ptw_selesai, name='ptw_selesai'),
    path('ptw/export-excel/', ptw_export_excel, name='ptw_export_excel'),   # <-- baru
    path('ptw/export-pdf/', ptw_export_pdf, name='ptw_export_pdf'),         # <-- baru

    # STRUKTUR ORGANISASI


    # RTPM
    path('rtpm/', rtpm_dashboard, name='rtpm_dashboard'),
    path('rtpm/tambah-jadwal/', rtpm_tambah_jadwal, name='rtpm_tambah_jadwal'),
    path('rtpm/hapus-jadwal/<int:id>/', rtpm_hapus_jadwal, name='rtpm_hapus_jadwal'),
    path('rtpm/input-pelaksanaan/<int:jadwal_id>/', rtpm_input_pelaksanaan, name='rtpm_input_pelaksanaan'),
    path('rtpm/edit-pelaksanaan/<int:jadwal_id>/', rtpm_edit_pelaksanaan, name='rtpm_edit_pelaksanaan'),
    path('rtpm/export-excel/', rtpm_export_excel, name='rtpm_export_excel'),
    path('rtpm/export-pdf/', rtpm_export_pdf, name='rtpm_export_pdf'),     # <-- baru


    path('knowledge-search/', knowledge_search, name='knowledge_search'),
]

# Static files (hanya untuk development)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT if settings.STATIC_ROOT else settings.STATICFILES_DIRS[0])
# Konfigurasi tambahan otomatis agar Django lokal mau melayani folder media/
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
