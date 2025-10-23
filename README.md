# UTS Event Aggregator — FastAPI + SQLite + Docker

## Deskripsi
Proyek ini merupakan implementasi sistem **Event Aggregator** yang berfungsi untuk menerima, menyimpan, dan mengelola batch event dari berbagai sumber dengan mekanisme **at-least-once delivery**.  
Sistem menerapkan **idempotency dan deduplication** agar event duplikat tidak diproses lebih dari satu kali.  
Selain itu, sistem menjamin **ordering** melalui queue FIFO dan melakukan **retry otomatis** jika penyimpanan event gagal. Sistem juga menyediakan endpoint statistik untuk pemantauan performa.

---

## Cara Build dan Run

| Langkah | Perintah | Keterangan |
|:--------|:----------|:------------|
| 1 | `docker build -t uts-aggregator .` | Membangun image dari Dockerfile |
| 2 | `docker run -p 8080:8080 uts-aggregator` | Menjalankan container |

Aplikasi dapat diakses melalui: 🌐 **http://localhost:8080**

---

## Endpoint API

| Method | Endpoint | Deskripsi | Contoh Output |
|:-------|:----------|:-----------|:----------------|
| `POST` | `/publish` | Menerima batch event untuk diproses dan disimpan | `{ "status": "ok" }` |
| `GET` | `/events` | Mengambil semua event yang tersimpan (dapat difilter per topic) | `[ { "topic": "...", "payload": {...} } ]` |
| `GET` | `/stats` | Menampilkan statistik jumlah event, duplikat, topik aktif, dan uptime | `{ "received": 100, "duplicate_dropped": 10, "uptime": 120.5 }` |

---

## Asumsi Sistem

| No | Asumsi | Penjelasan |
|:--:|:--------|:------------|
| 1 | Pengiriman event bersifat *at-least-once* | Event yang sama bisa dikirim lebih dari sekali |
| 2 | Setiap event memiliki ID unik (`event_id`) | Digunakan untuk mendeteksi duplikasi |
| 3 | Sistem bersifat *idempotent* | Event dengan ID sama tidak diproses ulang |
| 4 | SQLite digunakan untuk penyimpanan dedup | Menjamin persistensi meskipun container di-restart |
| 5 | FastAPI digunakan untuk API server | Framework ringan dan cepat berbasis async |

---

## Keputusan Desain

| No | Fitur | Penjelasan |
|:--:|:------|:------------|
| 1 | **Idempotency** | Setiap event memiliki `event_id` unik, sehingga event yang sama tidak diproses ulang. |
| 2 | **Dedup Store** | SQLite digunakan untuk menyimpan event unik dan mendeteksi duplikasi, sehingga persistensi tetap terjaga meski container di-restart. |
| 3 | **Ordering** | Event diproses secara FIFO melalui **asyncio queue**, sehingga urutan pengiriman dari klien dipertahankan. |
| 4 | **Retry** | Jika penyimpanan event gagal (misal error database), sistem akan mencoba hingga **3 kali** sebelum menandai gagal, agar delivery lebih andal. |

---

## Analisis Performa dan Metrik

- **Metrik utama:**  
  - `received` → jumlah event yang diterima  
  - `unique_processed` → jumlah event unik yang berhasil disimpan  
  - `duplicate_dropped` → jumlah event duplikat yang diabaikan  
  - `topics` → daftar topik aktif  
  - `uptime` → waktu berjalan container (detik)  

- **Hasil pengujian:**  
  - Batch test 1000 event → **waktu proses < 5 detik**  
  - Restart container → event lama tetap dikenali sebagai duplikat  
  - Retry → event gagal disimpan dicoba 3 kali sebelum di-drop  

- **Kesimpulan:**  
  Sistem mampu menangani load tinggi, mendeteksi duplikat, menjaga urutan event, dan memastikan event tersimpan dengan mekanisme retry.

---

## Pengujian

Unit test dilakukan menggunakan **pytest**:

| File | Pengujian | Tujuan |
|:------|:-----------|:--------|
| `test_api.py` | Pengujian endpoint `/publish`, `/events`, `/stats` | Validasi fungsi utama API |
| `test_dedup.py` | Pengujian SQLiteEventStore dan deteksi duplikat | Memastikan idempotency berjalan |
| Batch Test (1000 events) | Uji performa | Memastikan waktu proses < 5 detik |
| Persistence Test | Restart container | Verifikasi store tetap mengenali duplikat lama |

---

## Diagram Arsitektur (Sederhana)
+------------------+ +-------------------+
| Client/API | ----> | FastAPI Server |
| (Publish Event) | | (Async Queue) |
+------------------+ +-------------------+
|
v
+-------------------+
| SQLiteEventStore |
| (Dedup + Persist) |
+-------------------+
|
v
+-----------+
| Metrics/ |
| Stats API |
+-----------+


---

## Referensi (APA 7th Edition)

- Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1995). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley Professional.  
- Fowler, M. (2018). *Refactoring: Improving the Design of Existing Code* (2nd ed.). Addison-Wesley Professional.  
- Lutz, M. (2013). *Learning Python* (5th ed.). O'Reilly Media.  
- FastAPI. (n.d.). *FastAPI Documentation*. https://fastapi.tiangolo.com/  
- aiosqlite. (n.d.). *aiosqlite Documentation*. https://aiosqlite.omnilib.dev/
