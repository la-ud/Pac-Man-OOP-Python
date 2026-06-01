# 🟡 PAC-MAN OOP Edition v3

A retro-style Pac-Man game built with **Python** and **Pygame**, designed to demonstrate advanced **Object-Oriented Programming (OOP)** concepts while maintaining classic arcade gameplay.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green)
![OOP](https://img.shields.io/badge/OOP-Advanced-orange)

---

## 🎮 Preview

> Add your gameplay screenshot here

```text
assets/
└── preview.png
```

```md
![Gameplay](assets/preview.png)
```

---

## ✨ Features

* Retro Pac-Man visual style
* Smooth tile-locked movement system
* Animated Pac-Man mouth
* Four unique ghosts:

  * Blinky
  * Pinky
  * Inky
  * Clyde
* Power Pellets
* Particle effects
* Procedural retro sound effects (no external audio files required)
* Pause system
* Win / Game Over screen
* High Score tracking
* State Machine game flow
* Scanline arcade effect

---

## 🧠 OOP Concepts Implemented

This project intentionally demonstrates multiple Object-Oriented Programming concepts.

### 1. Class and Object

Examples:

* `PacMan`
* `Ghost`
* `GameEngine`
* `Renderer`
* `ScoreManager`

---

### 2. Inheritance

```python
class Ghost(Entity):
    ...

class Blinky(Ghost):
    ...

class Pinky(Ghost):
    ...
```

All ghost types inherit from the base `Ghost` class.

---

### 3. Abstract Base Class (ABC)

```python
class Entity(ABC):
```

The `Entity` class defines common behavior for all movable game objects.

---

### 4. Polymorphism

Each ghost implements its own targeting behavior:

```python
def get_target(self, pacman):
```

Examples:

* Blinky → directly chases Pac-Man
* Pinky → predicts movement
* Inky → semi-random targeting
* Clyde → alternates between chase and retreat

---

### 5. Class Attribute & Decorator

Class attributes:

```python
CELL_SIZE
FPS
LIVES
```

Property decorators:

```python
@property
def pixel_x(self):
```

---

### 6. NamedTuple

```python
Position = namedtuple(...)
Color = namedtuple(...)
```

Used to represent positions and RGB colors.

---

### 7. Design Pattern

#### Singleton Pattern

```python
class GameConfig
```

Ensures only one configuration instance exists.

#### Observer Pattern

```python
EventBus
```

Used for communication between game systems:

* score updates
* life loss
* level progression
* pellet effects

---

## 🎵 Sound System

This game generates arcade-style sound effects programmatically.

Included effects:

* Waka-Waka
* Power Pellet
* Ghost Eaten
* Death
* Game Over
* Victory Theme
* Dynamic Siren

No external sound files are required.

---

## 🕹 Controls

| Key   | Action       |
| ----- | ------------ |
| W / ↑ | Move Up      |
| S / ↓ | Move Down    |
| A / ← | Move Left    |
| D / → | Move Right   |
| P     | Pause        |
| ESC   | Back to Menu |
| Q     | Quit         |

---

## 🏗 Project Architecture

```text
GameEngine
│
├── Renderer
├── SFXEngine
├── ParticleSystem
├── ScoreManager
│
├── PacMan
│
└── Ghost
    ├── Blinky
    ├── Pinky
    ├── Inky
    └── Clyde
```

---

## 🚀 Installation

### Clone Repository

```bash
git clone https://github.com/your-username/pacman-oop.git
cd pacman-oop
```

### Install Dependencies

```bash
pip install pygame
```

### Run Game

```bash
python pacman_oop.py
```

---

## 🎯 Learning Objectives

This project was created to:

* Practice Object-Oriented Programming
* Implement Design Patterns in Python
* Understand game loops and state machines
* Learn collision handling using tile-based movement
* Explore procedural sound generation
* Build a complete interactive application using Pygame

---

## 📚 Technologies Used

* Python 3
* Pygame
* Object-Oriented Programming
* Design Patterns
* Procedural Audio Generation

---

## 👨‍💻 Author

Developed as an Object-Oriented Programming project inspired by the classic Pac-Man arcade game.

---

## 📄 License

This project is intended for educational and learning purposes.
