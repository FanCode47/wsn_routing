# WSN Routing Protocols

Симуляція протоколів маршрутизації для бездротових сенсорних мереж (Wireless Sensor Networks).

## Реалізовані протоколи

### LEACH
**Low-Energy Adaptive Clustering Hierarchy** - базовий кластерний протокол.

- Ротація Cluster Heads для рівномірного споживання енергії
- Агрегація даних в кластерах
- Single-hop від CH до sink

**Використання:**
```python
from router import LEACH
leach = LEACH(*nodes, n_cluster=6)
```

### APTEEN
**Adaptive Periodic Threshold-sensitive Energy Efficient sensor Network** - event-driven протокол.

- Базується на LEACH (кластери + ротація)
- Передача лише важливих даних (Hard Threshold)
- Передача лише при значних змінах (Soft Threshold)
- Періодичні оновлення (Count Time)

**Використання:**
```python
from router import APTEEN
apteen = APTEEN(*nodes, n_cluster=6, 
                hard_threshold=50.0, 
                soft_threshold=2.0, 
                count_time=10)
```

Детальна документація: [APTEEN.md](APTEEN.md)

## Швидкий старт

```python
from router import APTEEN
from distribution import simple_loader, uniform_in_square

# Створити мережу
sink = (0, 0)
nodes = simple_loader(sink, uniform_in_square(100, 100, sink))

# Ініціалізувати протокол
apteen = APTEEN(*nodes, n_cluster=5)
apteen.initialize()

# Симуляція
while len(apteen.alive_non_sinks) > 0:
    apteen.execute()
    print(f"Alive nodes: {len(apteen.alive_non_sinks)}")
```

## Тести

```bash
# Швидкий тест APTEEN
python test_apteen_quick.py

# Повний тест APTEEN з візуалізацією
python test_apteen.py

# Тест LEACH
python test_leach.py

# Порівняння протоколів
python compare_leach_and_apteen.py
```

## Налаштування через environment variables

```bash
# Snapshots
export SNAPSHOT_STEP=10      # зберігати кожні 10 раундів
export SNAPSHOT_GIF=1        # створити GIF

# Topology
export TOPO_STEP=20          # зберігати топологію кожні 20 раундів
export TOPO_GIF=1            # створити GIF

python test_apteen.py
```

## Структура проекту

```
wsn_routing/
├── router/
│   ├── __init__.py
│   ├── node.py              # Базовий клас Node
│   ├── router.py            # Базовий Router
│   ├── common.py            # Утиліти
│   ├── leach/
│   │   ├── leach.py         # LEACH
│   │   ├── hierarchical.py  # LEACHPrim, LEACHGreedy
│   │   └── ...
│   └── apteen.py            # APTEEN (НОВИЙ!)
├── distribution.py          # Генератори топології
├── test_*.py               # Тести
├── compare_*.py            # Порівняння
└── Results/                # Результати симуляцій
```

## Генератори топології

```python
from distribution import *

# Рівномірний розподіл у квадраті
nodes = simple_loader(sink, uniform_in_square(200, 100, sink, "left-bottem"))

# Рівномірний розподіл у колі
nodes = simple_loader(sink, uniform_in_circle(200, 100, sink))

# Вздовж лінії електропередач
nodes = simple_loader(sink, power_line_naive(
    n_relay=5, d_relay=100, d_jitter_max=10, 
    phi_max=0.3, n_sensors_per_relay=20, r_max=80, sink=sink
))
```

## Параметри Node

```python
Node.default_energy_max = 0.5       # Дж - початкова енергія
Node.default_e0_tx = 50e-9          # Дж/біт - передача
Node.default_e0_rx = 50e-9          # Дж/біт - прийом
Node.default_alive_threshold = 0.01  # Дж - поріг "живий"
```

## Вихідні файли

Результати зберігаються в `Results/run_YYYYMMDD_HHMMSS/`:
- `snapshots/` - графіки кількості живих вузлів
- `topology/` - графіки топології мережі
- `*.gif` - анімації (якщо включено)
- `compare_*.png` - порівняння протоколів

## Залежності

```bash
pip install numpy matplotlib
pip install imageio pillow  # опціонально для GIF
```

## Приклад порівняння

```python
from router import LEACH, APTEEN

# LEACH - передає завжди
leach = LEACH(*nodes, n_cluster=6)

# APTEEN - передає вибірково
apteen = APTEEN(*nodes, n_cluster=6,
                hard_threshold=50.0,
                soft_threshold=2.0,
                count_time=10)
```

**Очікувані результати:**
- LEACH: більше передач, менший lifetime
- APTEEN: менше передач, більший lifetime

## Ліцензія

Див. [LICENSE](LICENSE)
