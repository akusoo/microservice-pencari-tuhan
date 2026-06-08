  
**PROPOSAL FINAL PROJECT**

*Mata Kuliah Arsitektur Microservice dan Aplikasinya*

**LIBRARY MICROSERVICE SYSTEM**

*Sistem Perpustakaan Digital Berbasis Arsitektur Microservice*

**Disusun Oleh:**

| No | Nama | NRP |
| :---: | ----- | :---: |
| 1 | Aqsha Fadhli Azhim | 5053231023 |
| 2 | Muhammad Faizul Muttaqin Wahyudi | 5053231005 |
| 3 | Rausyan Fikri Muhammad | 5053231027 |

| Mata Kuliah | Arsitektur Microservice dan Aplikasinya |
| :---- | :---- |
| **Semester** | Genap 2025/2026 |
| **Tahun Akademik** | 2025/2026 |

**PROGRAM STUDI TEKNIK INFORMATIKA**  
**FAKULTAS TEKNOLOGI INFORMASI**  
**2026**

# **BAB I: PENDAHULUAN**

## **1.1 Latar Belakang**

Perpustakaan merupakan salah satu pusat informasi dan literasi yang memiliki peran penting dalam mendukung kegiatan akademik dan pengembangan pengetahuan. Namun, banyak perpustakaan, khususnya di lingkungan kampus, masih menerapkan sistem pengelolaan peminjaman buku secara manual atau menggunakan aplikasi monolitik yang sulit dikembangkan dan tidak scalable. Hal ini mengakibatkan proses pencatatan peminjaman, pengembalian, dan perhitungan denda menjadi lambat, rentan kesalahan, serta sulit dipantau secara real-time.

Seiring perkembangan teknologi perangkat lunak modern, arsitektur microservice menjadi solusi yang banyak diadopsi untuk membangun sistem yang modular dan mudah dikembangkan. Dengan memecah aplikasi menjadi beberapa service kecil yang independen, setiap modul dapat dikembangkan, di-deploy, dan di-scale secara terpisah sesuai dengan kebutuhan masing-masing domain bisnis.

Library Microservice System dikembangkan sebagai sistem perpustakaan digital yang memanfaatkan arsitektur microservice. Sistem ini memungkinkan pengelolaan buku, anggota, peminjaman, dan denda secara terstruktur dan transparan. Dengan pendekatan ini, setiap fitur dapat berjalan secara independen sehingga sistem menjadi lebih modular, mudah dipelihara, dan memiliki skalabilitas yang lebih baik.

## **1.2 Rumusan Masalah**

* Bagaimana merancang arsitektur microservice yang efektif untuk sistem perpustakaan digital?

* Bagaimana implementasi komunikasi antar service dalam pengelolaan peminjaman dan denda?

* Bagaimana mengelola autentikasi dan otorisasi pengguna dengan peran berbeda (member, librarian, admin) dalam arsitektur microservice?

* Bagaimana memastikan konsistensi data antar service yang berjalan secara independen, khususnya antara Loan Service dan Fine Service?

## **1.3 Tujuan Proyek**

* Merancang dan mengimplementasikan sistem perpustakaan digital berbasis microservice yang mencakup empat domain utama: Buku, Anggota, Peminjaman, dan Denda.

* Menerapkan best practice dalam pengembangan RESTful API untuk setiap microservice menggunakan FastAPI.

* Mengimplementasikan mekanisme autentikasi dan otorisasi yang aman menggunakan JWT dengan refresh token rotation.

* Menerapkan pola API Gateway sebagai single entry point dengan validasi token terpusat.

* Mendokumentasikan arsitektur sistem dan API endpoint secara lengkap menggunakan OpenAPI/Swagger.

## **1.4 Manfaat Proyek**

* Memberikan pengalaman praktis dalam pengembangan sistem berbasis microservice dengan Python FastAPI.

* Memahami tantangan dan solusi dalam komunikasi antar service, terutama dalam transaksi yang melibatkan beberapa service.

* Mengaplikasikan konsep DevOps dan containerisasi melalui Docker dan Docker Compose dalam deployment microservice.

* Menghasilkan sistem perpustakaan digital yang dapat menjadi referensi pengembangan sistem informasi di lingkungan akademik.

# **BAB II: TINJAUAN PUSTAKA**

## **2.1 Arsitektur Microservice**

Microservice adalah pendekatan arsitektur perangkat lunak di mana aplikasi dibangun sebagai kumpulan layanan kecil yang berjalan secara independen. Setiap service memiliki tanggung jawab bisnis yang spesifik (single responsibility), dapat di-deploy secara mandiri, dan berkomunikasi satu sama lain melalui API yang terdefinisi dengan baik. Pendekatan ini berbeda dengan arsitektur monolitik yang menggabungkan seluruh fungsionalitas dalam satu codebase tunggal.

Karakteristik utama microservice meliputi: (1) loose coupling antar service, (2) high cohesion dalam setiap service, (3) database per service untuk menjamin independensi data, dan (4) komunikasi melalui protokol standar seperti HTTP/REST atau message broker.

## **2.2 FastAPI sebagai Framework Microservice**

FastAPI adalah framework web modern berbahasa Python yang dibangun di atas Starlette dan Pydantic. Framework ini mendukung pemrograman asynchronous, memiliki performa tinggi yang setara dengan Node.js dan Go, serta menyediakan auto-generated documentation melalui OpenAPI dan Swagger UI. Karakteristik ini membuat FastAPI sangat cocok untuk pengembangan microservice.

## **2.3 JWT Authentication & Refresh Token Rotation**

JSON Web Token (JWT) adalah standar terbuka untuk pertukaran informasi secara aman antara pihak-pihak dalam bentuk JSON yang ditandatangani secara digital. Dalam arsitektur microservice, JWT umum digunakan sebagai mekanisme autentikasi karena bersifat stateless dan mudah dipropagasikan antar service. Untuk meningkatkan keamanan, implementasi refresh token rotation diterapkan agar token lama tidak dapat digunakan kembali (mencegah replay attack).

## **2.4 API Gateway Pattern**

API Gateway adalah pola desain yang berperan sebagai single entry point untuk seluruh permintaan client menuju microservice. Gateway bertanggung jawab atas routing, validasi token, rate limiting, dan logging terpusat. Pola ini menyederhanakan komunikasi client dengan sistem multi-service dan memberikan lapisan keamanan tambahan.

## **2.5 RESTful API**

REST (Representational State Transfer) adalah gaya arsitektur untuk membangun web service yang memanfaatkan protokol HTTP. API RESTful menggunakan HTTP method (GET, POST, PUT, DELETE) untuk operasi CRUD serta format JSON sebagai standar pertukaran data antar sistem.

## **2.6 Teknologi yang Digunakan**

| Komponen | Teknologi | Keterangan |
| ----- | ----- | ----- |
| **Backend Framework** | FastAPI \+ Uvicorn | Async REST API framework Python |
| **Database Migration**  | Alembic  | Version control skema database & sync antar environment  |
| **Validasi Data** | Pydantic v2 | Schema validation & serialization |
| **Database** | SQLite (dev) / PostgreSQL (prod) | RDBMS dengan SQLAlchemy ORM |
| **Autentikasi** | JWT  | Access token & refresh token |
| **Password Hashing** | passlib\[bcrypt\] | Hashing password sebelum disimpan |
| **Service Communication** | httpx | HTTP client async untuk komunikasi antar service |
| **Containerisasi** | Docker \+ Docker Compose | Isolasi dan orkestrasi service |
| **API Gateway** | FastAPI sebagai proxy | Single entry point & token validation |
| **Frontend** | HTML \+ Axios | SPA dengan auto-refresh token interceptor |
| **Dokumentasi API** | Swagger / OpenAPI 3.0 | Auto-generated docs dari FastAPI |

# **BAB III: DESKRIPSI SISTEM**	

## **3.1 Gambaran Umum Sistem**

Library Microservice System adalah platform perpustakaan digital yang memungkinkan pengelola untuk mendata buku dan anggota, memproses peminjaman dan pengembalian buku, serta menghitung denda keterlambatan secara otomatis. Sistem ini terdiri dari satu API Gateway dan lima service utama yang masing-masing bertanggung jawab atas domain bisnis spesifik.

## **3.2 Arsitektur Sistem**

Sistem dirancang dengan pola API Gateway sebagai single entry point untuk seluruh request dari client. API Gateway memvalidasi JWT token, kemudian meneruskan request ke microservice yang sesuai disertai header X-User-ID dan X-User-Role untuk keperluan otorisasi di service tujuan. Setiap microservice memiliki database-nya sendiri (Database per Service pattern) untuk memastikan loose coupling antar service. Komunikasi antar service dilakukan secara sinkron melalui httpx untuk operasi yang memerlukan respons langsung, seperti saat Loan Service memverifikasi keberadaan buku di Book Service.

## **3.3 Daftar Service**

| Service | Port | Fungsi |
| ----- | :---: | ----- |
| **API Gateway** | 8000 | Entry point, routing request, dan validasi JWT token |
| **Auth Service** | 8001 | Register, login, JWT, refresh token, bcrypt password hashing |
| **Book Service** | 8002 | CRUD buku dan manajemen kategori buku |
| **Member Service** | 8003 | Manajemen profil member dan status keanggotaan |
| **Loan Service** | 8004 | Proses peminjaman, pengembalian, dan riwayat peminjaman |
| **Fine Service** | 8005 | Perhitungan denda keterlambatan dan pembayaran denda |

## **3.4 Materi Perkuliahan yang Diimplementasikan**

| Materi Perkuliahan | Implementasi |
| ----- | ----- |
| **FastAPI \+ Pydantic \+ Async** | Semua service menggunakan async endpoint dan Pydantic schema |
| **Database Migration**  | Alembic per service untuk version control skema, auto-upgrade saat container start  |
| **Router & Dependency Injection** | APIRouter per service, Depends() untuk auth middleware |
| **JWT Authentication** | Access token (15 menit) \+ refresh token (7 hari) |
| **Refresh Token Rotation** | Token lama dihapus tiap refresh untuk mencegah replay attack |
| **Password Hashing (bcrypt)** | Password di-hash dengan bcrypt sebelum disimpan ke database |
| **HttpOnly Cookie** | Refresh token disimpan di HttpOnly cookie, bukan localStorage |
| **API Gateway Pattern** | FastAPI sebagai proxy dengan validasi token terpusat |
| **RBAC (Role-Based Access Control)** | Role member/librarian/admin membatasi akses endpoint tertentu |
| **Error Handling & Status Code** | HTTPException dengan status code semantik di semua service |
| **Service-to-Service Auth** | Gateway meneruskan X-User-ID dan X-User-Role ke downstream service |
| **Database per Service** | Setiap service memiliki database independen untuk loose coupling |
| **Containerization** | Docker Compose untuk orkestrasi multi-container |

# **BAB IV: SPESIFIKASI MODUL DAN SERVICE**

Library Microservice System terdiri dari empat modul utama yang masing-masing menangani domain bisnis tertentu. Setiap modul terdiri dari satu microservice yang berdiri sendiri, dengan database terpisah, dan saling berkomunikasi melalui REST API yang dikoordinasikan oleh API Gateway.

## **Modul 1: Manajemen Buku (Book Service)**

Service ini bertanggung jawab atas seluruh pengelolaan data buku di perpustakaan, mencakup penambahan, pengubahan, penghapusan, dan pencarian buku. Setiap buku memiliki atribut seperti judul, penulis, ISBN, kategori, stok tersedia, dan deskripsi singkat. Service ini juga memvalidasi ketersediaan stok buku ketika dipanggil oleh Loan Service saat proses peminjaman berlangsung.

### **Endpoint API**

| Method | Endpoint | Deskripsi |
| :---: | ----- | ----- |
| **GET** | /books | Mengambil seluruh daftar buku yang tersedia |
| **GET** | /books/{id} | Mengambil detail buku berdasarkan ID |
| **POST** | /books | Menambahkan buku baru ke katalog (admin/librarian) |
| **PUT** | /books/{id} | Mengubah data buku berdasarkan ID (admin/librarian) |
| **DELETE** | /books/{id} | Menghapus buku dari katalog (admin) |
| **GET** | /books/search | Pencarian buku berdasarkan judul, penulis, atau kategori |
| **PATCH** | /books/{id}/stock | Update stok buku (dipanggil oleh Loan Service) |

## **Modul 2: Manajemen Anggota (Member Service)**

Service ini mengelola data anggota perpustakaan, termasuk profil, status keanggotaan, dan riwayat keanggotaan. Setiap member memiliki status aktif/non-aktif/diblokir yang menentukan kemampuannya untuk meminjam buku. Status diblokir umumnya diberikan kepada member yang memiliki denda belum dibayar.

### **Endpoint API**

| Method | Endpoint | Deskripsi |
| :---: | ----- | ----- |
| **GET** | /members | Mengambil seluruh daftar anggota (librarian/admin) |
| **GET** | /members/{id} | Mengambil detail anggota berdasarkan ID |
| **GET** | /members/me | Mengambil profil anggota yang sedang login |
| **POST** | /members | Menambahkan anggota baru (admin/librarian) |
| **PUT** | /members/{id} | Mengubah data anggota berdasarkan ID |
| **PATCH** | /members/{id}/status | Mengubah status keanggotaan (aktif/blokir) |
| **DELETE** | /members/{id} | Menghapus anggota dari sistem (admin) |

## **Modul 3: Peminjaman (Loan Service)**

Service ini menangani seluruh siklus hidup peminjaman buku, mulai dari permintaan peminjaman, pencatatan tanggal jatuh tempo, hingga proses pengembalian. Saat permintaan peminjaman dibuat, service ini berkomunikasi dengan Book Service untuk memverifikasi stok dan dengan Member Service untuk memastikan status keanggotaan masih aktif. Setelah peminjaman dikonfirmasi, stok buku akan dikurangi secara otomatis.

### **Endpoint API**

| Method | Endpoint | Deskripsi |
| :---: | ----- | ----- |
| **POST** | /loans | Membuat permintaan peminjaman buku baru |
| **GET** | /loans | Mengambil seluruh daftar peminjaman (librarian/admin) |
| **GET** | /loans/me | Mengambil riwayat peminjaman user yang sedang login |
| **GET** | /loans/{id} | Mengambil detail peminjaman berdasarkan ID |
| **PATCH** | /loans/{id}/return | Memproses pengembalian buku |
| **PATCH** | /loans/{id}/extend | Perpanjangan masa pinjam |
| **GET** | /loans/overdue | Mengambil daftar peminjaman yang terlambat |

## **Modul 4: Denda (Fine Service)**

Service ini mengelola perhitungan denda keterlambatan pengembalian buku dan proses pembayarannya. Ketika pengembalian buku dilakukan setelah tanggal jatuh tempo, Loan Service akan memanggil Fine Service untuk membuat record denda secara otomatis. Besaran denda dihitung berdasarkan jumlah hari keterlambatan dikalikan tarif harian yang dapat dikonfigurasi.

### **Endpoint API**

| Method | Endpoint | Deskripsi |
| :---: | ----- | ----- |
| **POST** | /fines | Membuat record denda (dipanggil otomatis oleh Loan Service) |
| **GET** | /fines | Mengambil seluruh daftar denda (librarian/admin) |
| **GET** | /fines/me | Mengambil daftar denda user yang sedang login |
| **GET** | /fines/{id} | Mengambil detail denda berdasarkan ID |
| **PATCH** | /fines/{id}/pay | Memproses pembayaran denda |
| **GET** | /fines/unpaid | Mengambil daftar denda yang belum dibayar |

## **Modul Pendukung: Auth Service & API Gateway**

Auth Service menangani proses registrasi, login, logout, serta penerbitan dan refresh JWT token. Password disimpan menggunakan hashing bcrypt, dan refresh token disimpan dalam HttpOnly cookie untuk mencegah serangan XSS. Refresh token rotation diterapkan untuk meningkatkan keamanan.

### **Endpoint Auth Service**

| Method | Endpoint | Deskripsi |
| :---: | ----- | ----- |
| **POST** | /auth/register | Mendaftarkan akun pengguna baru |
| **POST** | /auth/login | Autentikasi pengguna dan menerbitkan token |
| **POST** | /auth/refresh | Memperbarui access token menggunakan refresh token |
| **POST** | /auth/logout | Mengakhiri sesi pengguna dan mencabut token |
| **GET** | /auth/me | Mengambil informasi user yang sedang login |

API Gateway berperan sebagai single entry point yang memvalidasi JWT token, melakukan routing request ke service tujuan, dan meneruskan informasi user melalui header X-User-ID dan X-User-Role. Pendekatan ini menyederhanakan komunikasi antara client dengan sistem multi-service serta memberikan kontrol terpusat atas autentikasi dan otorisasi.

# **BAB V: RENCANA IMPLEMENTASI**

## **5.1 Tahapan Pengerjaan**

| Sprint | Aktivitas | Durasi | Deliverable |
| :---: | ----- | :---: | ----- |
| **Sprint 1** | Perancangan arsitektur sistem, setup environment Docker, dan inisialisasi repository setiap service | 1 Minggu | Architecture diagram, Docker setup, repo struktur |
| **Sprint 2** | Implementasi Auth Service dengan JWT, refresh token rotation, dan password hashing bcrypt | 1 Minggu | Auth API berjalan, JWT validation |
| **Sprint 3** | Implementasi Book Service & Member Service dengan CRUD dan RBAC | 1 Minggu | Book & Member API berjalan |
| **Sprint 4** | Implementasi Loan Service & Fine Service dengan komunikasi antar service | 1 Minggu | Loan & Fine API berjalan terintegrasi |
| **Sprint 5** | Integrasi API Gateway, frontend React, testing end-to-end, dan dokumentasi akhir | 1 Minggu | Sistem terintegrasi penuh, dokumentasi lengkap |

## **5.2 Pembagian Tugas Tim**

* Backend Developer: Implementasi RESTful API untuk setiap microservice menggunakan FastAPI dan Pydantic.

* DevOps Engineer: Konfigurasi Docker, Docker Compose, dan deployment pipeline untuk multi-container environment.

* Database Designer: Perancangan schema database per service dengan SQLAlchemy ORM.

* Frontend & Documentation: Pengembangan UI React dengan Axios interceptor, dan penulisan dokumentasi Swagger/OpenAPI.

## **5.3 Kriteria Keberhasilan**

* Seluruh endpoint API berfungsi sesuai spesifikasi yang telah didefinisikan dalam BAB IV.

* Setiap service dapat berjalan secara independen dalam container Docker yang terpisah.

* Autentikasi JWT dengan refresh token rotation berjalan dengan baik di seluruh service.

* API Gateway mampu memvalidasi token dan meneruskan request dengan benar ke service tujuan.

* Komunikasi antar service (Loan-Book, Loan-Member, Loan-Fine) berjalan tanpa error.

* Dokumentasi API lengkap dan dapat diakses melalui Swagger UI pada setiap service.

* Sistem dapat menangani concurrent request dengan benar tanpa data inconsistency.

# **BAB VI: PENUTUP**

## **6.1 Kesimpulan**

Proposal ini menjelaskan rencana pembangunan Library Microservice System, sebuah sistem perpustakaan digital yang dibangun di atas arsitektur microservice menggunakan Python FastAPI. Sistem ini terdiri dari satu API Gateway dan lima service utama (Auth, Book, Member, Loan, Fine) yang masing-masing dirancang dengan prinsip single responsibility, loose coupling, dan high cohesion sebagai karakteristik utama arsitektur microservice yang baik.

Dengan memanfaatkan teknologi modern seperti FastAPI untuk REST API, JWT dengan refresh token rotation untuk autentikasi yang aman, bcrypt untuk password hashing, serta Docker dan Docker Compose untuk containerisasi, proyek ini diharapkan dapat menjadi contoh implementasi microservice yang komprehensif dan dapat dijadikan referensi pengembangan sistem informasi perpustakaan di dunia nyata.

## **6.2 Harapan**

Final project ini diharapkan dapat memberikan pemahaman mendalam mengenai tantangan dan solusi dalam pengembangan sistem berbasis microservice, mencakup desain arsitektur, komunikasi antar service, manajemen autentikasi dan otorisasi terdistribusi, serta penerapan konsep containerisasi. Selain sebagai pemenuhan tugas akhir mata kuliah, hasil proyek ini juga diharapkan dapat menjadi portofolio yang membuktikan kemampuan tim dalam membangun aplikasi skala enterprise dengan arsitektur modern yang relevan terhadap kebutuhan industri saat ini.

Surabaya, Mei 2026

**Tim Pengembang**