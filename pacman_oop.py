"""
╔══════════════════════════════════════════════════════════════╗
║           PAC-MAN  -  OOP Python Edition  v3                 ║
║  Modul OOP yang digunakan:                                   ║
║   1. Class and Object         (semua entitas game)           ║
║   2. Inheritance              (Ghost -> Blinky/Pinky/Inky)  ║
║   3. Abstract Base Class      (Entity sebagai ABC)           ║
║   4. Class Attribute & Decorator (GameConfig, @property)    ║
║   5. Design Pattern           (Observer + Singleton)         ║
╚══════════════════════════════════════════════════════════════╝

  ARSITEKTUR GERAKAN (Tile-Locked Interpolation):
  ─────────────────────────────────────────────────
  • Setiap entitas punya tile sumber (src) dan tile tujuan (dst)
    dalam koordinat integer grid.
  • `progress` (0.0 → 1.0) = seberapa jauh perjalanan src→dst.
  • Posisi piksel = lerp(src, dst, progress).
  • Keputusan arah HANYA diambil saat progress mencapai 1.0
    (entitas tiba di tile tujuan), lalu src←dst dan pilih dst baru.
  • Tidak ada ambiguitas float, tidak ada threshold — gerakan
    selalu 100% sinkron dengan grid.
"""

import pygame
import sys
import random
import math
import time
import struct
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from collections import namedtuple

# ─────────────────────────────────────────────────────────────
# NAMEDTUPLE  (bonus modul 6)
# ─────────────────────────────────────────────────────────────
Position = namedtuple("Position", ["x", "y"])
Color    = namedtuple("Color",    ["r", "g", "b"])

# ─────────────────────────────────────────────────────────────
# MODUL 5 – DESIGN PATTERN: SINGLETON  (GameConfig)
# ─────────────────────────────────────────────────────────────
class GameConfig:
    """Singleton — satu-satunya instance konfigurasi game."""
    _instance: Optional["GameConfig"] = None

    # ── MODUL 4: Class Attribute ──
    CELL_SIZE: int = 28
    COLS:      int = 21
    ROWS:      int = 23
    FPS:       int = 60
    LIVES:     int = 3

    # ── Kecepatan dalam tile-per-frame ──
    PACMAN_SPEED: float = 0.13   # tile/frame
    GHOST_SPEED:  float = 0.09
    GHOST_SCARED_SPEED: float = 0.055

    C_WALL   = Color(33,  33, 222)
    C_DOT    = Color(255, 185, 176)
    C_PACMAN = Color(255, 255,   0)
    C_SCORE  = Color(255, 184,  82)
    C_WIN    = Color(0,   255, 128)
    C_OVER   = Color(255,  50,  50)
    C_BORDER = Color(0,   180, 255)

    GHOST_COLORS = [
        Color(255,   0,   0),   # Blinky
        Color(255, 180, 255),   # Pinky
        Color(  0, 255, 255),   # Inky
        Color(255, 165,   0),   # Clyde
    ]

    def __new__(cls) -> "GameConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def screen_width(self) -> int:
        return self.COLS * self.CELL_SIZE

    @property
    def screen_height(self) -> int:
        return (self.ROWS + 4) * self.CELL_SIZE

    @staticmethod
    def to_rgb(c: Color) -> Tuple[int, int, int]:
        return (c.r, c.g, c.b)


cfg = GameConfig()

# ─────────────────────────────────────────────────────────────
# MODUL 5 – DESIGN PATTERN: OBSERVER  (EventBus)
# ─────────────────────────────────────────────────────────────
class EventObserver(ABC):
    @abstractmethod
    def on_event(self, name: str, data=None) -> None: ...

class EventBus:
    def __init__(self):
        self._listeners: dict = {}

    def subscribe(self, name: str, obs: "EventObserver") -> None:
        self._listeners.setdefault(name, []).append(obs)

    def publish(self, name: str, data=None) -> None:
        for obs in self._listeners.get(name, []):
            obs.on_event(name, data)

bus = EventBus()

# ─────────────────────────────────────────────────────────────
# PETA GAME
# ─────────────────────────────────────────────────────────────
# 0=kosong, 1=dinding, 2=dot, 3=power-pellet, 9=pintu hantu
RAW_MAP = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,3,1,1,2,1,1,1,2,1,1,1,2,1,1,1,2,1,1,3,1],
    [1,2,1,1,2,1,1,1,2,1,1,1,2,1,1,1,2,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,1,1,2,1,2,1,1,1,1,1,1,1,2,1,2,1,1,2,1],
    [1,2,2,2,2,1,2,2,2,2,1,2,2,2,2,1,2,2,2,2,1],
    [1,1,1,1,2,1,1,1,0,0,0,0,0,1,1,1,2,1,1,1,1],
    [1,1,1,1,2,1,0,0,0,0,0,0,0,0,0,1,2,1,1,1,1],
    [1,1,1,1,2,0,0,1,1,9,9,9,1,1,0,0,2,1,1,1,1],
    [0,0,0,0,2,0,0,1,0,0,0,0,0,1,0,0,2,0,0,0,0],
    [1,1,1,1,2,0,0,1,1,1,1,1,1,1,0,0,2,1,1,1,1],
    [1,1,1,1,2,0,0,0,0,0,0,0,0,0,0,0,2,1,1,1,1],
    [1,1,1,1,2,1,0,0,1,1,1,1,1,0,0,1,2,1,1,1,1],
    [1,1,1,1,2,1,0,0,0,0,0,0,0,0,0,1,2,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,2,1,1,2,1,1,1,2,1,1,1,2,1,1,1,2,1,1,2,1],
    [1,3,2,1,2,2,2,2,2,2,0,2,2,2,2,2,2,1,2,3,1],
    [1,1,2,1,2,1,2,1,1,1,1,1,1,1,2,1,2,1,2,1,1],
    [1,2,2,2,2,1,2,2,2,2,1,2,2,2,2,1,2,2,2,2,1],
    [1,2,1,1,1,1,1,1,2,1,1,1,2,1,1,1,1,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

def _is_blocked(col: int, row: int, game_map: List[List[int]]) -> bool:
    """Cek apakah tile (col, row) adalah dinding. Integer murni, tanpa float."""
    if row < 0 or row >= cfg.ROWS or col < 0 or col >= cfg.COLS:
        return True
    return game_map[row][col] == 1


# ─────────────────────────────────────────────────────────────
# MODUL 3 – ABSTRACT BASE CLASS: Entity
# ─────────────────────────────────────────────────────────────
class Entity(ABC):
    """
    Base class tile-locked.
    Setiap entitas bergerak dari src_tile → dst_tile dengan
    progress 0→1. Saat progress=1 tile tiba, pilih tile berikutnya.
    """

    def __init__(self, tile_x: int, tile_y: int):
        # Posisi tile integer (sumber & tujuan)
        self.src_x: int = tile_x
        self.src_y: int = tile_y
        self.dst_x: int = tile_x
        self.dst_y: int = tile_y
        # Progres interpolasi 0.0–1.0
        self.progress: float = 1.0   # mulai sudah "tiba" di tile
        # Arah gerak saat ini (tile delta)
        self.dir_x: int = 0
        self.dir_y: int = 0
        self.speed: float = 0.13

    # ── MODUL 4: @property ──
    @property
    def pixel_x(self) -> int:
        """Posisi piksel interpolasi antara src dan dst."""
        x = self.src_x + (self.dst_x - self.src_x) * self.progress
        return int(x * cfg.CELL_SIZE + cfg.CELL_SIZE // 2)

    @property
    def pixel_y(self) -> int:
        y = self.src_y + (self.dst_y - self.src_y) * self.progress
        return int(y * cfg.CELL_SIZE + cfg.CELL_SIZE // 2)

    @property
    def tile(self) -> Position:
        """Tile integer terdekat saat ini."""
        return Position(self.dst_x, self.dst_y)

    def reset_to(self, tile_x: int, tile_y: int) -> None:
        self.src_x = self.dst_x = tile_x
        self.src_y = self.dst_y = tile_y
        self.progress = 1.0
        self.dir_x = self.dir_y = 0

    @abstractmethod
    def update(self, game_map: List[List[int]]) -> None: ...

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None: ...


# ─────────────────────────────────────────────────────────────
# MODUL 1 – CLASS & OBJECT: PacMan
# ─────────────────────────────────────────────────────────────
class PacMan(Entity):
    """
    Pac-Man dengan sistem tile-locked.

    Cara kerja:
    1. Pemain menekan tombol → next_dir tersimpan.
    2. Saat progress >= 1.0 (tiba di tile):
       a. Coba terapkan next_dir ke tile berikutnya.
          Jika tidak ada dinding → arah baru diterima, next_dir dikosongkan.
       b. Jika next_dir tidak bisa (dinding), coba teruskan dir_x/dir_y lama.
       c. Jika keduanya dinding → Pac-Man berhenti di tile ini.
    3. Animasi mulut berjalan hanya saat bergerak.
    """

    MOUTH_SPEED: float = 0.16   # MODUL 4: Class Attribute

    def __init__(self, start_x: int, start_y: int):
        super().__init__(start_x, start_y)
        self.start_tile = Position(start_x, start_y)
        self.speed      = cfg.PACMAN_SPEED
        self.next_dir_x: int = 0
        self.next_dir_y: int = 0
        self._anim_t:  float = 0.0
        self._moving:  bool  = False
        # Arah wajah untuk gambar (tidak diubah saat berhenti)
        self._face_x: int = 1
        self._face_y: int = 0

    def reset(self) -> None:
        self.reset_to(self.start_tile.x, self.start_tile.y)
        self.next_dir_x = self.next_dir_y = 0
        self._moving = False

    def set_direction(self, dx: int, dy: int) -> None:
        """Catat arah yang diminta pemain. Disimpan hingga bisa dieksekusi."""
        self.next_dir_x = dx
        self.next_dir_y = dy

    # ─────────────────────────────────────────────────────────
    # UPDATE — tile-locked, tidak ada float collision ambiguity
    # ─────────────────────────────────────────────────────────
    def update(self, game_map: List[List[int]]) -> None:
        self.progress += self.speed

        if self.progress >= 1.0:
            # Tiba di tile tujuan — tile tujuan menjadi tile sumber
            self.progress = 1.0
            self.src_x = self.dst_x
            self.src_y = self.dst_y

            moved = False

            # ── Coba next_dir terlebih dahulu ──
            if self.next_dir_x != 0 or self.next_dir_y != 0:
                nx = self.src_x + self.next_dir_x
                ny = self.src_y + self.next_dir_y
                # Wrap terowongan horizontal
                nx = nx % cfg.COLS
                if not _is_blocked(nx, ny, game_map):
                    self.dir_x    = self.next_dir_x
                    self.dir_y    = self.next_dir_y
                    self.dst_x    = nx
                    self.dst_y    = ny
                    self.progress = 0.0
                    self._face_x  = self.dir_x
                    self._face_y  = self.dir_y
                    # Hapus next_dir setelah berhasil dieksekusi
                    # TAPI: simpan jika arah baru = arah lama (tetap valid)
                    if self.dir_x == self.next_dir_x and self.dir_y == self.next_dir_y:
                        self.next_dir_x = self.next_dir_y = 0
                    moved = True

            # ── Jika next_dir gagal atau tidak ada, teruskan dir lama ──
            if not moved and (self.dir_x != 0 or self.dir_y != 0):
                nx = self.src_x + self.dir_x
                ny = self.src_y + self.dir_y
                nx = nx % cfg.COLS
                if not _is_blocked(nx, ny, game_map):
                    self.dst_x    = nx
                    self.dst_y    = ny
                    self.progress = 0.0
                    moved = True
                # Jika dinding → progress tetap 1.0, Pac-Man berhenti

            self._moving = moved

        # ── Animasi mulut hanya saat bergerak ──
        if self._moving:
            self._anim_t += self.MOUTH_SPEED

    @property
    def mouth_open(self) -> float:
        return abs(math.sin(self._anim_t)) * 42.0 if self._moving else 8.0

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = self.pixel_x, self.pixel_y
        r   = cfg.CELL_SIZE // 2 - 2
        ang = math.degrees(math.atan2(-self._face_y, self._face_x))
        mo  = self.mouth_open

        # Lingkaran utama
        pygame.draw.circle(surface, cfg.to_rgb(cfg.C_PACMAN), (cx, cy), r)
        # Mulut (potongan segitiga)
        if mo > 2:
            pygame.draw.polygon(surface, (0, 0, 0), [
                (cx, cy),
                (cx + r * math.cos(math.radians(ang + mo)),
                 cy - r * math.sin(math.radians(ang + mo))),
                (cx + r * math.cos(math.radians(ang - mo)),
                 cy - r * math.sin(math.radians(ang - mo))),
            ])
        # Mata kecil
        ex = cx + int(r * 0.38 * math.cos(math.radians(ang + 68)))
        ey = cy - int(r * 0.38 * math.sin(math.radians(ang + 68)))
        pygame.draw.circle(surface, (0, 0, 0), (ex, ey), 2)


# ─────────────────────────────────────────────────────────────
# MODUL 2 – INHERITANCE: Ghost (base) + 4 subclass
# ─────────────────────────────────────────────────────────────
class Ghost(Entity):
    """
    Hantu dengan tile-locked movement.
    Setiap kali tiba di tile baru, pilih tile tujuan berikutnya
    dengan algoritma shortest-path ke target (override get_target).
    """

    SCARED_DURATION: int = 300   # MODUL 4: Class Attribute

    def __init__(self, tile_x: int, tile_y: int, color: Color, name: str):
        super().__init__(tile_x, tile_y)
        self.start_tile   = Position(tile_x, tile_y)
        self.color        = color
        self.name         = name
        self.speed        = cfg.GHOST_SPEED
        self.scared       = False
        self.scared_timer = 0
        self._anim_t      = 0.0
        # Arah awal acak
        self.dir_x = random.choice([-1, 0, 1])
        self.dir_y = 0 if self.dir_x != 0 else random.choice([-1, 1])

    def reset(self) -> None:
        self.reset_to(self.start_tile.x, self.start_tile.y)
        self.scared       = False
        self.scared_timer = 0
        self.dir_x        = random.choice([-1, 1])
        self.dir_y        = 0

    def scare(self) -> None:
        self.scared       = True
        self.scared_timer = self.SCARED_DURATION
        self.speed        = cfg.GHOST_SCARED_SPEED

    @abstractmethod
    def get_target(self, pacman: PacMan) -> Position: ...

    def _pick_next_tile(self, game_map: List[List[int]],
                        target: Position) -> None:
        """
        Dari tile saat ini (src_x, src_y), pilih satu tile tetangga
        yang paling dekat ke target. Tidak boleh berbalik arah kecuali
        tidak ada pilihan lain.
        """
        cx, cy = self.src_x, self.src_y
        reverse = (-self.dir_x, -self.dir_y)
        best_dist = float("inf")
        best_dx = best_dy = 0
        found = False

        # Acak urutan untuk variasi gerak
        candidates = [(1,0),(-1,0),(0,1),(0,-1)]
        random.shuffle(candidates)

        for dx, dy in candidates:
            if (dx, dy) == reverse:
                continue
            nx = (cx + dx) % cfg.COLS
            ny = cy + dy
            if _is_blocked(nx, ny, game_map):
                continue
            dist = math.hypot(nx - target.x, ny - target.y)
            # Mode takut: pilih yang TERJAUH dari target
            if self.scared:
                dist = -dist
            if dist < best_dist:
                best_dist = dist
                best_dx, best_dy = dx, dy
                found = True

        if not found:
            # Buntu total → balik arah
            best_dx, best_dy = reverse

        nx = (cx + best_dx) % cfg.COLS
        ny = cy + best_dy
        if not _is_blocked(nx, ny, game_map):
            self.dir_x = best_dx
            self.dir_y = best_dy
            self.dst_x = nx
            self.dst_y = ny
            self.progress = 0.0

    def update(self, game_map: List[List[int]],
               pacman: Optional[PacMan] = None) -> None:
        # Update scared timer
        if self.scared:
            self.scared_timer -= 1
            if self.scared_timer <= 0:
                self.scared = False
                self.speed  = cfg.GHOST_SPEED

        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 1.0
            self.src_x = self.dst_x
            self.src_y = self.dst_y
            if pacman:
                self._pick_next_tile(game_map, self.get_target(pacman))

        self._anim_t += 0.20

    # Signature Entity.update dipenuhi via override di atas
    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = self.pixel_x, self.pixel_y
        r      = cfg.CELL_SIZE // 2 - 2
        blink  = self.scared and self.scared_timer < 80

        if self.scared:
            body = (100, 100, 255) if (not blink or int(self._anim_t * 3) % 2) \
                   else (255, 255, 255)
        else:
            body = cfg.to_rgb(self.color)

        # Badan oval
        pygame.draw.ellipse(surface, body,
                            (cx - r, cy - r, 2*r, int(1.65*r)))
        # Rok bergelombang
        n = 4
        for i in range(n):
            wx = cx - r + i * (2*r // n) + (r // n)
            wy = cy + int(0.55 * r)
            pygame.draw.circle(surface, body, (wx, wy + r // 3), r // n)

        # Mata
        for sign in (-1, 1):
            ex = cx + sign * int(r * 0.35)
            ey = cy - int(r * 0.22)
            if self.scared:
                pygame.draw.line(surface, (255,255,255),
                                 (ex-3, ey-3),(ex+3, ey+3), 2)
                pygame.draw.line(surface, (255,255,255),
                                 (ex+3, ey-3),(ex-3, ey+3), 2)
            else:
                pygame.draw.circle(surface, (255,255,255), (ex, ey), 4)
                pygame.draw.circle(surface, (0, 0, 200), (ex+1, ey+1), 2)


# ── MODUL 2 – Subclass Ghost (Polimorfisme get_target) ──
class Blinky(Ghost):
    """Mengejar langsung posisi Pac-Man."""
    def get_target(self, p: PacMan) -> Position:
        return p.tile

class Pinky(Ghost):
    """Mencoba berada 4 tile di depan Pac-Man."""
    def get_target(self, p: PacMan) -> Position:
        return Position(p.tile.x + p._face_x * 4,
                        p.tile.y + p._face_y * 4)

class Inky(Ghost):
    """Target di 2 tile depan Pac-Man + offset acak."""
    def get_target(self, p: PacMan) -> Position:
        return Position(p.tile.x + p._face_x * 2 + random.randint(-2, 2),
                        p.tile.y + p._face_y * 2 + random.randint(-2, 2))

class Clyde(Ghost):
    """Mengejar bila jauh, kabur bila dekat."""
    def get_target(self, p: PacMan) -> Position:
        dist = math.hypot(self.src_x - p.tile.x, self.src_y - p.tile.y)
        return p.tile if dist > 8 else Position(0, cfg.ROWS - 1)


# ─────────────────────────────────────────────────────────────
# MODUL 1 – CLASS: ScoreManager (Observer)
# ─────────────────────────────────────────────────────────────
class ScoreManager(EventObserver):
    DOT_SCORE        = 10
    PELLET_SCORE     = 50
    GHOST_SCORE_BASE = 200

    def __init__(self):
        self.score        = 0
        self.lives        = cfg.LIVES
        self.level        = 1
        self._ghost_combo = 1
        bus.subscribe("dot_eaten",    self)
        bus.subscribe("pellet_eaten", self)
        bus.subscribe("ghost_eaten",  self)
        bus.subscribe("life_lost",    self)
        bus.subscribe("level_up",     self)

    def on_event(self, name: str, data=None) -> None:
        if name == "dot_eaten":
            self.score += self.DOT_SCORE
        elif name == "pellet_eaten":
            self.score += self.PELLET_SCORE
            self._ghost_combo = 1
        elif name == "ghost_eaten":
            self.score += self.GHOST_SCORE_BASE * self._ghost_combo
            self._ghost_combo = min(self._ghost_combo * 2, 8)
        elif name == "life_lost":
            self.lives -= 1
        elif name == "level_up":
            self.level += 1


# ─────────────────────────────────────────────────────────────
# SFX ENGINE – chiptune prosedural (tanpa file eksternal)
# ─────────────────────────────────────────────────────────────
class SFXEngine:
    SR = 22050

    def __init__(self):
        pygame.mixer.pre_init(self.SR, -16, 1, 512)
        pygame.mixer.init()
        self._s: dict = {}
        self._waka_phase = 0
        self._last_waka  = 0.0
        self._siren_ch   = None
        self._siren_snd  = None
        self._scared_snd = None
        self._build()

    def _pack(self, samples: list) -> pygame.mixer.Sound:
        return pygame.mixer.Sound(buffer=struct.pack(f"<{len(samples)}h", *samples))

    def _square(self, freq, dur, vol=0.4, duty=0.5) -> list:
        n, per = int(self.SR * dur), self.SR / max(freq, 1)
        return [int(32767 * vol * (1 if (i % per) / per < duty else -1)
                    * max(0.0, 1.0 - (i / n)**2))
                for i in range(n)]

    def _sweep(self, f0, f1, dur, vol=0.42) -> list:
        n, out, ph = int(self.SR * dur), [], 0.0
        for i in range(n):
            freq = f0 + (f1 - f0) * (i / n)
            env  = math.sin(math.pi * i / n)
            ph  += 2 * math.pi * freq / self.SR
            val  = 1.0 if math.sin(ph) >= 0 else -1.0
            out.append(int(32767 * vol * env * val))
        return out

    def _noise(self, dur, vol=0.3) -> list:
        n = int(self.SR * dur)
        return [int(32767 * vol * max(0, 1 - i/n) * random.uniform(-1, 1))
                for i in range(n)]

    def _build(self) -> None:
        self._s["waka_hi"]  = self._pack(self._sweep(800, 380, 0.065))
        self._s["waka_lo"]  = self._pack(self._sweep(380, 800, 0.065))
        self._s["pellet"]   = self._pack(self._sweep(200, 1300, 0.17, 0.55))
        ge = []
        for f in [900, 700, 500, 340]:
            ge += self._square(f, 0.052, 0.5)
        self._s["ghost_eat"]= self._pack(ge)
        self._s["death"]    = self._pack(
            self._sweep(580, 70, 0.48, 0.55) + self._noise(0.15, 0.4))
        go = []
        for f in [523, 415, 330, 262, 220, 185]:
            go += self._square(f, 0.11, 0.44) + [0]*700
        self._s["game_over"]= self._pack(go)
        wi = []
        for f in [523, 659, 784, 1047, 784, 1047]:
            wi += self._square(f, 0.095, 0.5) + [0]*350
        self._s["win"]      = self._pack(wi)
        intro = []
        for f in [523, 659, 523, 659, 784, 659, 784, 1047]:
            intro += self._square(f, 0.075, 0.45) + [0]*260
        self._s["intro"]    = self._pack(intro)
        siren = []
        for _ in range(5):
            siren += self._sweep(255, 315, 0.22, 0.14)
            siren += self._sweep(315, 255, 0.22, 0.14)
        self._siren_snd     = self._pack(siren)
        scr = []
        for _ in range(5):
            scr += self._sweep(175, 215, 0.16, 0.17)
            scr += self._sweep(215, 175, 0.16, 0.17)
        self._scared_snd    = self._pack(scr)

    def play(self, name: str, vol: float = 1.0) -> None:
        s = self._s.get(name)
        if s:
            s.set_volume(vol)
            s.play()

    def play_waka(self) -> None:
        k = "waka_hi" if self._waka_phase == 0 else "waka_lo"
        self._waka_phase ^= 1
        self._s[k].set_volume(0.55)
        self._s[k].play()

    def start_siren(self, scared: bool = False) -> None:
        snd = self._scared_snd if scared else self._siren_snd
        if self._siren_ch:
            self._siren_ch.stop()
        self._siren_ch = snd.play(-1)

    def stop_siren(self) -> None:
        if self._siren_ch:
            self._siren_ch.stop()
            self._siren_ch = None


# ─────────────────────────────────────────────────────────────
# Partikel visual
# ─────────────────────────────────────────────────────────────
class Particle:
    __slots__ = ("x","y","vx","vy","life","color","size")
    def __init__(self, x, y, color):
        self.x=x; self.y=y
        a=random.uniform(0,2*math.pi); s=random.uniform(1.5,4.5)
        self.vx=math.cos(a)*s; self.vy=math.sin(a)*s
        self.life=random.randint(22,50); self.color=color
        self.size=random.randint(2,5)
    def update(self):
        self.x+=self.vx; self.y+=self.vy; self.vy+=0.12
        self.life-=1; return self.life>0
    def draw(self,s):
        pygame.draw.circle(s,self.color,(int(self.x),int(self.y)),max(1,self.size))

class ParticleSystem:
    def __init__(self): self._p=[]
    def emit(self,x,y,col,n=12):
        for _ in range(n): self._p.append(Particle(x,y,col))
    def update_and_draw(self,s):
        self._p=[p for p in self._p if p.update()]
        for p in self._p: p.draw(s)


# ─────────────────────────────────────────────────────────────
# MODUL 1 – CLASS: Renderer
# ─────────────────────────────────────────────────────────────
class Renderer:
    def __init__(self, surface, font_lg, font_md, font_sm):
        self.surface = surface
        self.font_lg = font_lg
        self.font_md = font_md
        self.font_sm = font_sm
        self._stars  = [(random.randint(0, cfg.screen_width),
                         random.randint(0, cfg.screen_height),
                         random.random()) for _ in range(70)]
        # Scanline overlay (dibuat sekali saja untuk performa)
        self._scan = pygame.Surface((cfg.screen_width, cfg.screen_height),
                                    pygame.SRCALPHA)
        for y in range(0, cfg.screen_height, 3):
            pygame.draw.line(self._scan, (0,0,0,50),
                             (0,y), (cfg.screen_width, y), 1)

    def draw_map(self, game_map):
        cs = cfg.CELL_SIZE
        for row in range(cfg.ROWS):
            for col in range(cfg.COLS):
                cell = game_map[row][col]
                rx, ry = col*cs, row*cs
                if cell == 1:
                    pygame.draw.rect(self.surface, cfg.to_rgb(cfg.C_WALL),
                                     (rx+1,ry+1,cs-2,cs-2), border_radius=4)
                    pygame.draw.rect(self.surface, cfg.to_rgb(cfg.C_BORDER),
                                     (rx+1,ry+1,cs-2,cs-2), 1, border_radius=4)
                elif cell == 2:
                    pygame.draw.circle(self.surface, cfg.to_rgb(cfg.C_DOT),
                                       (rx+cs//2, ry+cs//2), 3)
                elif cell == 3:
                    t  = time.time() * 3
                    pr = int(7 + 2*math.sin(t + col + row))
                    pygame.draw.circle(self.surface, (255,200,100),
                                       (rx+cs//2, ry+cs//2), pr)
                    pygame.draw.circle(self.surface, (255,255,200),
                                       (rx+cs//2, ry+cs//2), max(1,pr-3))

    def draw_hud(self, sm: ScoreManager):
        hy = cfg.ROWS * cfg.CELL_SIZE + 6
        pygame.draw.rect(self.surface, (10,10,30),
                         (0, hy-4, cfg.screen_width, 70))
        pygame.draw.line(self.surface, cfg.to_rgb(cfg.C_BORDER),
                         (0, hy-4),(cfg.screen_width, hy-4), 2)
        s = self.font_md.render(f"SCORE  {sm.score:06d}", True,
                                cfg.to_rgb(cfg.C_SCORE))
        self.surface.blit(s, (12, hy))
        lv = self.font_sm.render(f"LV {sm.level}", True, (180,255,180))
        self.surface.blit(lv, (cfg.screen_width//2-20, hy+6))
        for i in range(sm.lives):
            lx = cfg.screen_width - 30 - i*26
            ly = hy + 10
            pygame.draw.circle(self.surface, cfg.to_rgb(cfg.C_PACMAN),(lx,ly),9)
            pygame.draw.polygon(self.surface,(0,0,0),
                                [(lx,ly),(lx+9,ly-5),(lx+9,ly+5)])

    def draw_scanlines(self):
        self.surface.blit(self._scan, (0,0))

    def draw_overlay(self, text, sub, color):
        ov = pygame.Surface((cfg.screen_width, cfg.screen_height), pygame.SRCALPHA)
        ov.fill((0,0,0,165))
        self.surface.blit(ov,(0,0))
        t = time.time()
        if int(t*2)%2==0:
            ms = self.font_lg.render(text, True, color)
            self.surface.blit(ms,(cfg.screen_width//2-ms.get_width()//2,
                                  cfg.screen_height//2-60))
        ss = self.font_md.render(sub, True, (200,200,200))
        self.surface.blit(ss,(cfg.screen_width//2-ss.get_width()//2,
                              cfg.screen_height//2+10))

    def draw_pause(self):
        ov = pygame.Surface((cfg.screen_width, cfg.screen_height), pygame.SRCALPHA)
        ov.fill((0,0,0,150)); self.surface.blit(ov,(0,0))
        t = time.time()
        if int(t*2)%2==0:
            ps = self.font_lg.render("PAUSE", True, (255,220,0))
            self.surface.blit(ps,(cfg.screen_width//2-ps.get_width()//2,
                                  cfg.screen_height//2-40))
        hs = self.font_md.render("P = LANJUT", True, (200,200,200))
        self.surface.blit(hs,(cfg.screen_width//2-hs.get_width()//2,
                              cfg.screen_height//2+20))

    def draw_title_screen(self, hi_score: int):
        self.surface.fill((0,0,0))
        t = time.time()
        for sx,sy,phase in self._stars:
            a = int(128+127*math.sin(t*2+phase*6))
            r = max(1, int(1+math.sin(t+phase*4)))
            pygame.draw.circle(self.surface,(a//4,a//4,a),(sx,sy),r)

        letters = "PAC-MAN"
        cols = [(255,255,0),(255,200,0),(255,160,0)]
        for i,ch in enumerate(letters):
            c  = cols[i%len(cols)]
            gw = self.font_lg.render(ch, True, (c[0]//4,c[1]//4,0))
            mw = self.font_lg.render(ch, True, c)
            off = int(5*math.sin(t*3+i))
            bx,by = 58+i*70, 80+off
            self.surface.blit(gw,(bx+3,by+3))
            self.surface.blit(mw,(bx,by))

        # Pac-Man animasi berjalan
        px = int(cfg.screen_width//2 + 110*math.sin(t))
        py = 230
        mo = abs(math.sin(t*8))*45
        pygame.draw.circle(self.surface, cfg.to_rgb(cfg.C_PACMAN),(px,py),22)
        if mo>3:
            pygame.draw.polygon(self.surface,(0,0,0),[
                (px,py),(px+22,py-int(22*math.sin(math.radians(mo)))),
                        (px+22,py+int(22*math.sin(math.radians(mo))))])

        lines = [
            ("TEKAN  ENTER  UNTUK  MAIN", (255,255,80),  310),
            ("WASD / ARROW KEYS = GERAK",  (100,200,255), 355),
            ("P = PAUSE  |  ESC = MENU",   (180,255,180), 385),
            (f"HIGH SCORE : {hi_score:06d}",(255,165,0),  430),
            ("Q = KELUAR",                  (180,180,180), 470),
        ]
        for txt,col,y in lines:
            if y==310 and int(t*2)%2==0: col=(255,255,255)
            s = self.font_md.render(txt, True, col)
            self.surface.blit(s,(cfg.screen_width//2-s.get_width()//2, y))

        oop = ["[ OOP Modules ]",
               "1.Class&Object  2.Inheritance  3.ABC",
               "4.ClassAttr+Decorator  5.DesignPattern"]
        for i,line in enumerate(oop):
            col=(80,160,80) if i==0 else (55,110,55)
            s = self.font_sm.render(line, True, col)
            self.surface.blit(s,(cfg.screen_width//2-s.get_width()//2,
                                 522+i*20))


# ─────────────────────────────────────────────────────────────
# MODUL 1 – CLASS: GameEngine (controller utama)
# ─────────────────────────────────────────────────────────────
class GameEngine:
    DEATH_DELAY: int = 100   # MODUL 4: Class Attribute

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("🟡  PAC-MAN  OOP Edition  v3")
        self.screen = pygame.display.set_mode(
            (cfg.screen_width, cfg.screen_height))
        self.clock  = pygame.time.Clock()

        try:
            fp = pygame.font.match_font("couriernew,courier,monospace")
            self.font_lg = pygame.font.Font(fp, 52)
            self.font_md = pygame.font.Font(fp, 22)
            self.font_sm = pygame.font.Font(fp, 16)
        except Exception:
            self.font_lg = pygame.font.SysFont("monospace", 52, bold=True)
            self.font_md = pygame.font.SysFont("monospace", 22)
            self.font_sm = pygame.font.SysFont("monospace", 16)

        self.renderer  = Renderer(self.screen, self.font_lg,
                                  self.font_md, self.font_sm)
        self.particles = ParticleSystem()
        self.sfx       = SFXEngine()
        self.score_mgr = ScoreManager()
        self.hi_score  = 0

        self.game_map:  List[List[int]] = []
        self.pacman:    Optional[PacMan] = None
        self.ghosts:    List[Ghost]      = []
        self.state:     str   = "title"
        self._paused:   bool  = False
        self._death_timer: int = 0
        self._last_waka:  float = 0.0
        self._scared_state: bool = False

        self._init_game()
        self.sfx.play("intro", 0.7)

    @staticmethod
    def _copy_map() -> List[List[int]]:
        return [row[:] for row in RAW_MAP]

    def _init_game(self) -> None:
        global bus
        bus = EventBus()   # reset bus agar listener lama tidak duplikat
        self.game_map  = self._copy_map()
        self.pacman    = PacMan(10, 17)
        self.ghosts    = [
            Blinky( 9,  9, cfg.GHOST_COLORS[0], "Blinky"),
            Pinky( 10,  9, cfg.GHOST_COLORS[1], "Pinky"),
            Inky(  11,  9, cfg.GHOST_COLORS[2], "Inky"),
            Clyde(  9, 11, cfg.GHOST_COLORS[3], "Clyde"),
        ]
        self.score_mgr      = ScoreManager()
        self._last_waka     = 0.0
        self._scared_state  = False
        self._paused        = False
        self.sfx.stop_siren()

    def _reset_positions(self) -> None:
        self.pacman.reset()
        for g in self.ghosts:
            g.reset()

    # ── Input: gunakan get_pressed untuk responsivitas maksimal ──
    def _poll_keys(self) -> None:
        """
        Baca tombol yang sedang DITEKAN setiap frame.
        Ini lebih responsif dari KEYDOWN event karena tidak
        terpengaruh key-repeat delay sistem operasi.
        """
        if self.state != "playing" or self._paused:
            return
        keys = pygame.key.get_pressed()
        if   keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.pacman.set_direction(-1, 0)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.pacman.set_direction( 1, 0)
        elif keys[pygame.K_UP]    or keys[pygame.K_w]: self.pacman.set_direction( 0,-1)
        elif keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.pacman.set_direction( 0, 1)

    def _handle_event(self, event: pygame.event.Event) -> None:
        """Tangani event satu kali (toggle, menu navigation)."""
        if event.type != pygame.KEYDOWN:
            return
        k = event.key

        if self.state == "title":
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = "playing"
                self.sfx.start_siren()
            elif k == pygame.K_q:
                pygame.quit(); sys.exit()

        elif self.state in ("over", "win"):
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.hi_score = max(self.hi_score, self.score_mgr.score)
                self._init_game()
                self.state = "title"
                self.sfx.play("intro", 0.7)
            elif k == pygame.K_q:
                pygame.quit(); sys.exit()

        elif self.state == "playing":
            if k == pygame.K_p:
                self._paused = not self._paused
                if self._paused:
                    self.sfx.stop_siren()
                else:
                    self.sfx.start_siren(self._scared_state)
            elif k == pygame.K_ESCAPE:
                self.hi_score = max(self.hi_score, self.score_mgr.score)
                self.sfx.stop_siren()
                self._init_game()
                self.state = "title"
                self.sfx.play("intro", 0.7)

    def _check_dots(self) -> None:
        p  = self.pacman
        tx, ty = p.tile
        if 0 <= tx < cfg.COLS and 0 <= ty < cfg.ROWS:
            cell = self.game_map[ty][tx]
            if cell == 2:
                self.game_map[ty][tx] = 0
                bus.publish("dot_eaten")
                self.particles.emit(p.pixel_x, p.pixel_y,
                                    cfg.to_rgb(cfg.C_DOT), 5)
            elif cell == 3:
                self.game_map[ty][tx] = 0
                bus.publish("pellet_eaten")
                self.sfx.play("pellet", 0.75)
                self.particles.emit(p.pixel_x, p.pixel_y, (255,200,50), 22)
                for g in self.ghosts:
                    g.scare()

    def _check_ghost_collision(self) -> None:
        p = self.pacman
        for g in self.ghosts:
            # Tabrakan berdasarkan tile, bukan piksel
            same_tile = (p.tile == g.tile or
                         (p.dst_x == g.src_x and p.dst_y == g.src_y and
                          g.dst_x == p.src_x and g.dst_y == p.src_y))
            if not same_tile:
                px_dist = math.hypot(g.pixel_x - p.pixel_x,
                                     g.pixel_y - p.pixel_y)
                if px_dist > cfg.CELL_SIZE * 0.75:
                    continue
            if g.scared:
                bus.publish("ghost_eaten")
                self.sfx.play("ghost_eat", 0.8)
                self.particles.emit(g.pixel_x, g.pixel_y,
                                    cfg.to_rgb(g.color), 28)
                g.reset()
            else:
                bus.publish("life_lost")
                self.sfx.stop_siren()
                self.sfx.play("death", 0.85)
                self.particles.emit(p.pixel_x, p.pixel_y, (255,255,0), 35)
                self.state        = "death"
                self._death_timer = self.DEATH_DELAY
                return

    def _check_win(self) -> bool:
        for row in self.game_map:
            if 2 in row or 3 in row:
                return False
        return True

    def _update_waka(self) -> None:
        if not self.pacman._moving:
            return
        now = time.time()
        if now - self._last_waka > 0.11:
            self.sfx.play_waka()
            self._last_waka = now

    def _update_siren(self) -> None:
        any_scared = any(g.scared for g in self.ghosts)
        if any_scared != self._scared_state:
            self._scared_state = any_scared
            self.sfx.start_siren(scared=any_scared)

    def run(self) -> None:
        while True:
            # ── Event (sekali per event: toggle & menu) ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self._handle_event(event)

            # ── Poll keys setiap frame (gerakan) ──
            self._poll_keys()

            self.screen.fill((0, 0, 0))

            # ─── STATE MACHINE ───
            if self.state == "title":
                self.renderer.draw_title_screen(self.hi_score)

            elif self.state == "playing":
                if not self._paused:
                    self.pacman.update(self.game_map)
                    self._check_dots()
                    self._update_waka()
                    self._update_siren()
                    for g in self.ghosts:
                        g.update(self.game_map, self.pacman)
                    self._check_ghost_collision()
                    if self._check_win():
                        bus.publish("level_up")
                        self.sfx.stop_siren()
                        self.sfx.play("win", 0.9)
                        self.state = "win"

                self.renderer.draw_map(self.game_map)
                self.pacman.draw(self.screen)
                for g in self.ghosts:
                    g.draw(self.screen)
                self.particles.update_and_draw(self.screen)
                self.renderer.draw_hud(self.score_mgr)
                self.renderer.draw_scanlines()
                if self._paused:
                    self.renderer.draw_pause()

            elif self.state == "death":
                self._death_timer -= 1
                self.renderer.draw_map(self.game_map)
                for g in self.ghosts:
                    g.draw(self.screen)
                self.particles.update_and_draw(self.screen)
                self.renderer.draw_hud(self.score_mgr)
                self.renderer.draw_scanlines()
                if self._death_timer <= 0:
                    if self.score_mgr.lives <= 0:
                        self.sfx.play("game_over", 0.9)
                        self.state = "over"
                    else:
                        self._reset_positions()
                        self.sfx.start_siren()
                        self.state = "playing"

            elif self.state == "win":
                self.renderer.draw_map(self.game_map)
                self.renderer.draw_hud(self.score_mgr)
                self.renderer.draw_overlay("YOU  WIN!",
                    "ENTER = MAIN LAGI   |   ESC = MENU",
                    cfg.to_rgb(cfg.C_WIN))

            elif self.state == "over":
                self.renderer.draw_map(self.game_map)
                self.renderer.draw_hud(self.score_mgr)
                self.renderer.draw_overlay("GAME  OVER",
                    "ENTER = MAIN LAGI   |   Q = KELUAR",
                    cfg.to_rgb(cfg.C_OVER))

            pygame.display.flip()
            self.clock.tick(cfg.FPS)


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("  PAC-MAN OOP Edition  v3  —  Tile-Locked Movement Fix")
    print()
    print("  ROOT CAUSE BUG (versi sebelumnya):")
    print("    1. is_wall() pakai round(float) → ambiguitas collision")
    print("    2. near_center threshold 0.45 terlalu lebar → snap salah posisi")
    print("    3. Sistem float bebas tidak sinkron dgn tile grid integer")
    print("    4. Input hanya dari KEYDOWN event → kena key-repeat delay OS")
    print()
    print("  SOLUSI (v3 — Tile-Locked Interpolation):")
    print("    • Setiap entitas punya src_tile dan dst_tile (int).")
    print("    • progress 0→1 = animasi, keputusan arah HANYA saat tiba.")
    print("    • Collision cek: integer tile, ZERO float ambiguity.")
    print("    • Input: pygame.key.get_pressed() setiap frame.")
    print("      → Responsif penuh, tanpa delay key-repeat OS.")
    print()
    print("  Kontrol: WASD / Arrow  |  P = Pause  |  ESC = Menu  |  Q = Quit")
    print("=" * 65)
    GameEngine().run()
