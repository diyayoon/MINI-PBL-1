# PeekABoo - Image Steganography

PeekABoo adalah aplikasi web sederhana untuk menyisipkan data gambar ke dalam gambar penampung dan mengambilnya kembali menggunakan teknik steganografi LSB 2-bit.

Project ini dibuat sebagai Mini PBL Semester 1 Program Studi Rekayasa Keamanan Siber.

## Fitur

- Enkripsi/penyisipan file gambar ke dalam gambar penampung.
- Dekripsi/ekstraksi data dari gambar stego.
- Secret key untuk proses XOR pada data sebelum disisipkan.
- Preview dan download hasil proses.
- Antarmuka web menggunakan HTML, CSS, dan JavaScript.

## Teknologi

- Python
- Flask
- Pillow
- HTML, CSS, dan JavaScript

## Struktur Project

```text
MINI-PBL-1/
├── Back-end/
│   ├── app.py
│   ├── stego.py
│   └── storage/
│       ├── uploads/
│       └── outputs/
├── Front-end/
│   ├── assets/
│   │   ├── background-web.jpg
│   │   └── logo-peekaboo.png
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── .gitignore
├── README.md
└── requirements.txt
```

Folder `storage/uploads` dan `storage/outputs` digunakan untuk menyimpan file selama aplikasi berjalan. File hasil upload dan pemrosesan tidak disertakan dalam repository.

## Persyaratan

- Python 3.10 atau lebih baru
- pip

## Instalasi dan Menjalankan Aplikasi

Jalankan perintah berikut dari folder utama project.

### 1. Buat virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Jalankan backend

Pastikan terminal masih berada di folder utama project, lalu jalankan:

```bash
python .\Back-end\app.py
```

Untuk Linux/macOS:

```bash
python Back-end/app.py
```

### 4. Buka aplikasi

Akses alamat berikut melalui browser:

```text
http://127.0.0.1:5000
```

## Alur Penggunaan

### Enkripsi

1. Pilih gambar asli yang ingin disembunyikan.
2. Pilih gambar penampung.
3. Masukkan secret key.
4. Jalankan proses enkripsi.
5. Download gambar stego yang dihasilkan.

### Dekripsi

1. Upload gambar stego.
2. Masukkan secret key yang sama dengan proses enkripsi.
3. Jalankan proses dekripsi.
4. Download file hasil ekstraksi.

## Format File

Aplikasi menerima file PNG, JPG, JPEG, dan WebP. Hasil gambar stego disimpan dalam format PNG.

## Catatan Implementasi

Project ini merupakan implementasi pembelajaran. Penyisipan data menggunakan LSB 2-bit, sedangkan proses XOR menggunakan keystream berbasis SHA-256. Mekanisme tersebut ditujukan untuk demonstrasi konsep dan bukan pengganti algoritma enkripsi modern untuk melindungi data sensitif.
