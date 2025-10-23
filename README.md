# 🚀 UTS Event Aggregator — FastAPI + SQLite + Docker

## 📘 Deskripsi
Proyek ini merupakan implementasi sistem **Event Aggregator** yang berfungsi untuk menerima, menyimpan, dan mengelola batch event dari berbagai sumber dengan mekanisme **at-least-once delivery**.  
Sistem menerapkan **idempotency dan deduplication** agar event duplikat tidak diproses lebih dari satu kali, serta dilengkapi dengan endpoint statistik untuk pemantauan performa.

---

## ⚙️ Cara Build dan Run

| Langkah | Perintah | Keterangan |
|:--------|:----------|:------------|
| 1 | `docker build -t uts-aggregator .` | Membangun image dari Dockerfile |
| 2 | `docker run -p 8080:8080 uts-aggregator` | Menjalankan container |
| 3 | (Opsional) `pytest -v` | Menjalankan unit test di dalam container |
| 4 | (Opsional) `docker-compose up --build` | Menjalankan sistem menggunakan docker-compose |

Aplikasi dapat diakses melalui:  
🌐 **http://localhost:8080**

---

## 🧩 Endpoint API

| Method | Endpoint | Deskripsi | Contoh Output |
|:-------|:----------|:-----------|:----------------|
| `POST` | `/publish` | Menerima batch event untuk diproses dan disimpan | `{ "status": "ok" }` |
| `GET` | `/events` | Mengambil semua event yang tersimpan (dapat difilter per topic) | `[ { "topic": "...", "payload": {...} } ]` |
| `GET` | `/stats` | Menampilkan statistik jumlah event, duplikat, dan topik aktif | `{ "received": 100, "duplicate_dropped": 10 }` |
| `GET` | `/health` | Mengecek status service | `{ "status": "healthy" }` |

---

## 💡 Asumsi Sistem

| No | Asumsi | Penjelasan |
|:--:|:--------|:------------|
| 1 | Pengiriman event bersifat *at-least-once* | Event yang sama bisa dikirim lebih dari sekali |
| 2 | Setiap event memiliki ID unik (`event_id`) | Digunakan untuk mendeteksi duplikasi |
| 3 | Sistem bersifat *idempotent* | Event dengan ID sama tidak diproses ulang |
| 4 | SQLite digunakan untuk penyimpanan dedup | Menjamin persistensi meskipun container di-restart |
| 5 | FastAPI digunakan untuk API server | Framework ringan dan cepat berbasis async |

---

## 🧪 Pengujian

Unit test dilakukan menggunakan **pytest** dan mencakup:

| File | Pengujian | Tujuan |
|:------|:-----------|:--------|
| `test_api.py` | Pengujian endpoint `/publish`, `/events`, `/stats` | Validasi fungsi utama API |
| `test_dedup.py` | Pengujian SQLiteEventStore dan deteksi duplikat | Memastikan idempotency berjalan |
| Batch Test (1000 events) | Uji performa | Memastikan waktu proses < 5 detik |
| Persistence Test | Restart container | Verifikasi store tetap mengenali duplikat lama |

Perintah:
```bash
pytest -v