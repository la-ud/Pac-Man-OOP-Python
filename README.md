🟡 Pac-Man OOP Python Edition v3
Sebuah clone game klasik Pac-Man yang dibangun murni menggunakan Python dan Pygame.
Proyek ini bukan sekadar game biasa, melainkan sebuah implementasi arsitektur perangkat
lunak yang menonjolkan prinsip Object-Oriented Programming (OOP), Design Patterns, dan
Procedural Audio.
Game ini menggunakan sistem pergerakan Tile-Locked Interpolation untuk memastikan
gerakan entitas 100% presisi dan tersinkronisasi dengan grid, menghilangkan bug collision
yang sering terjadi pada pergerakan berbasis float.
✨ Fitur Utama
● Tile-Locked Movement: Gerakan Pac-Man dan Hantu dikunci ke dalam grid (sumber ke
tujuan) menggunakan interpolasi progresif. Anti-nyangkut dan anti-tembus dinding!
● Individual Ghost AI: Keempat hantu memiliki sifat klasik aslinya. Blinky mengejar
langsung, Pinky memotong jalan, Inky menyergap, dan Clyde menjaga jarak.
● Procedural Chiptune SFX: Tidak memerlukan file audio eksternal (.wav/.mp3). Seluruh
efek suara (waka-waka, sirene, makan dot) di-sintesis secara prosedural langsung dari
kode!
● Retro Visuals: Dilengkapi dengan scanlines overlay, partikel visual saat memakan
hantu/dot, dan efek animasi smooth.
️ Implementasi OOP & Arsitektur
1. Class & Object: Struktur dasar untuk memisahkan logika GameEngine, Renderer, dan
Entity.
2. Inheritance & Polimorfisme: Pemisahan behavior AI hantu menggunakan subclassing
(Ghost -> Blinky, Pinky, Inky, Clyde) melalui override metode pencarian target.
3. Abstract Base Class (ABC): Penggunaan antarmuka abstrak pada kelas Entity dan
EventObserver.
4. Class Attribute & Decorator: Penggunaan @property untuk kalkulasi posisi piksel
dinamis dan Singleton config.
5. Design Patterns: Menggunakan Singleton untuk manajemen konfigurasi game
(GameConfig) dan Observer Pattern (EventBus) untuk sistem scoring yang decoupled.
🚀 Cara Menjalankan

Pastikan kamu sudah menginstal Python dan Pygame di komputermu.
1. Clone repositori ini.
2. Instal dependensi:
pip install pygame
3. Jalankan game:
python pacman_oop.py
🎮 Kontrol Game
● Gerak: Tombol Panah (Arrow Keys) / W, A, S, D
● Pause: P
● Kembali ke Menu: ESC
● Keluar: Q
