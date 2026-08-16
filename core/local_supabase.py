from django.db import connection
from datetime import datetime, date
import json
import random
import os
from supabase import create_client as supabase_original_client

class MockExecuteResult:
    def __init__(self, data):
        self.data = data

class LocalJobsTable:
    def __init__(self):
        self._filters = []
        self._params = []
        self._op = "SELECT"
        self._insert_data = None
        self._update_data = None
        self._single = False
        self._limit = None

    def __getattr__(self, name):
        # Fallback fleksibel jika views memanggil nama fungsi filter yang tidak terduga
        return self

    def select(self, cols="*"): self._op = "SELECT"; return self
    def insert(self, data): self._insert_data = data; self._op = "INSERT"; return self
    def update(self, data): self._update_data = data; self._op = "UPDATE"; return self
    def delete(self): self._op = "DELETE"; return self

    def eq(self, col, val):
        if val is not None and str(val).strip() != '':
            # Mapping otomatis jika mendeteksi request filter_jenis dari views
            target_col = "Jenis" if str(col).lower() in ["jenis", "filter_jenis"] else col
            target_col = "ID" if str(target_col).upper() == "ID" else target_col
            self._filters.append(f'"{target_col}" = %s')
            self._params.append(str(val))
        return self

    def gte(self, col, val):
        if val is not None and str(val).strip() != '':
            self._filters.append(f'"{col}"::date >= %s::date')
            self._params.append(str(val))
        return self

    def lte(self, col, val):
        if val is not None and str(val).strip() != '':
            self._filters.append(f'"{col}"::date <= %s::date')
            self._params.append(str(val))
        return self

    def ilike(self, col, val):
        if val is not None and str(val).strip() != '':
            target_col = "ID" if str(col).upper() == "ID" else col
            self._filters.append(f'"{target_col}" ILIKE %s')
            self._params.append(f"%{val}%")
        return self

    def order(self, col, desc=False): return self
    
    def limit(self, num):
        if num is not None:
            self._limit = int(num)
        return self
        
    def single(self): self._single = True; return self

    def execute(self):
        with connection.cursor() as cursor:
            res_data = []
            if self._op == "SELECT":
                where_clause = " WHERE " + " AND ".join(self._filters) if self._filters else ""
                
                # --- ATURAN AKUMULASI TOTAL TANPA BATAS ---
                # Jika views meminta limit khusus -> patuhi.
                # Jika ada filter pencarian (Tanggal, Jenis, SR) -> JANGAN PAKAI LIMIT (Buka akumulasi total data).
                # Jika dashboard utama sedang merangkum grafik -> JANGAN PAKAI LIMIT.
                # LIMIT 100 HANYA mengunci halaman tabel polosan agar tidak lemot saat pertama kali di-klik.
                limit_clause = ""
                if self._limit:
                    limit_clause = f" LIMIT {self._limit}"
                elif not self._filters:
                    limit_clause = " LIMIT 100"

                sql = f'SELECT * FROM "jobs" {where_clause} ORDER BY "ID" DESC {limit_clause}'
                cursor.execute(sql, self._params)
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    res_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                for row in res_data:
                    for k in list(row.keys()):
                        v = row[k]
                        if isinstance(v, (datetime, date)): row[k] = v.strftime('%Y-%m-%d')
                        row[k.lower()] = row[k]
                        row[k.upper()] = row[k]
                if self._single: res_data = res_data[0] if res_data else None

            elif self._op == "INSERT":
                item = self._insert_data
                if "ID" not in item or item["ID"] is None or str(item["ID"]).strip() == "":
                    random_hex = f"{random.randint(0x1000, 0xFFFF):X}"
                    prefix = "JOB"
                    if item.get("Jenis"):
                        parts = str(item["Jenis"]).split()
                        prefix = parts[0].upper() if len(parts) > 1 and parts[0].isalpha() else str(item["Jenis"])[:3].upper()
                    item["ID"] = f"{prefix}-{random_hex}"
                if "created_at" not in item:
                    item["created_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                cols = ", ".join([f'"{k}"' for k in item.keys()])
                vals = ", ".join(["%s"] * len(item))
                sql = f'INSERT INTO "jobs" ({cols}) VALUES ({vals}) RETURNING *'
                cursor.execute(sql, list(item.values()))
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    res_data = dict(zip(columns, cursor.fetchone()))
                    for k in list(res_data.keys()):
                        v = res_data[k]
                        if isinstance(v, (datetime, date)): res_data[k] = v.strftime('%Y-%m-%d')
                        res_data[k.lower()] = res_data[k]
                        res_data[k.upper()] = res_data[k]

            elif self._op == "UPDATE":
                set_clause = ", ".join([f'"{k}" = %s' for k in self._update_data.keys()])
                where_clause = " WHERE " + " AND ".join(self._filters) if self._filters else ""
                sql = f'UPDATE "jobs" SET {set_clause} {where_clause} RETURNING *'
                cursor.execute(sql, list(self._update_data.values()) + self._params)
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    res_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

            elif self._op == "DELETE":
                where_clause = " WHERE " + " AND ".join(self._filters) if self._filters else ""
                sql = f'DELETE FROM "jobs" {where_clause}'
                cursor.execute(sql, self._params)
                res_data = []

            return MockExecuteResult(res_data)

class LocalStorageBucket:
    def upload(self, path, file, file_options=None):
        try:
            base_dir = "/var/www/armor/media"
            clean_path = path.replace('var/www/armor/media/', '').replace('/var/www/armor/media/', '')
            final_path = os.path.join(base_dir, clean_path)
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            with open(final_path, 'wb') as f:
                f.write(file)
            return True
        except Exception: return False

    def get_public_url(self, path):
        clean_path = path.replace('var/www/armor/media/', '').replace('/var/www/armor/media/', '').lstrip('/')
        return f"/media/{clean_path}"

class LocalStorage:
    def from_(self, bucket_name): return LocalStorageBucket()

class HybridSupabaseClient:
    def __init__(self, url, key):
        self.real_client = supabase_original_client(url, key)
        self.storage = LocalStorage()

    def table(self, name):
        if name == "jobs":
            return LocalJobsTable()
        return self.real_client.table(name)

def create_client(url=None, key=None):
    if not url: url = os.getenv("SUPABASE_URL")
    if not key: key = os.getenv("SUPABASE_KEY")
    return HybridSupabaseClient(url, key)
