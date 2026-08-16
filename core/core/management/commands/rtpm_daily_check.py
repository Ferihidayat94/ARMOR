from django.core.management.base import BaseCommand
from datetime import date
import os
import requests
from core.local_supabase import create_client
from dotenv import load_dotenv

load_dotenv()

class Command(BaseCommand):
    help = 'Kirim pengingat RTPM hari ini dan update status overdue'

    def handle(self, *args, **options):
        # Koneksi ke Supabase
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        supabase = create_client(url, key)

        TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        today = date.today()
        today_str = today.isoformat()

        # 1. Ambil jadwal hari ini yang masih Pending
        today_jobs = supabase.table("rtpm_jadwal") \
            .select("*") \
            .eq("tanggal", today_str) \
            .eq("status", "Pending") \
            .execute()

        for job in today_jobs.data:
            # Kirim reminder ke Telegram
            msg = (f"🔔 *PENGINGAT RTPM HARI INI*\n\n"
                   f"🛠️ Peralatan: *{job['equipment']}*\n"
                   f"📋 Aktivitas: *{job['activity']}*\n"
                   f"📅 Tanggal: {today.strftime('%d-%m-%Y')}\n\n"
                   f"✅ Mohon laksanakan dan input hasilnya di ARMOR.")
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            self.stdout.write(f"Reminder: {job['equipment']}")

        # 2. Ambil jadwal yang sudah lewat dan masih Pending -> Overdue
        overdue_jobs = supabase.table("rtpm_jadwal") \
            .select("*") \
            .lt("tanggal", today_str) \
            .eq("status", "Pending") \
            .execute()

        for job in overdue_jobs.data:
            # Update status
            supabase.table("rtpm_jadwal").update({"status": "Overdue"}).eq("id", job["id"]).execute()
            # Kirim peringatan
            tgl_obj = date.fromisoformat(job['tanggal'])
            msg = (f"⚠️ *PERINGATAN RTPM TERLEWAT*\n\n"
                   f"🛠️ Peralatan: *{job['equipment']}*\n"
                   f"📋 Aktivitas: *{job['activity']}*\n"
                   f"📅 Jadwal: {tgl_obj.strftime('%d-%m-%Y')}\n\n"
                   f"❗ Segera laksanakan dan input hasilnya.")
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
            self.stdout.write(f"Overdue: {job['equipment']}")

        self.stdout.write(self.style.SUCCESS("Selesai."))