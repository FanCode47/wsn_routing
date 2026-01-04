# APTEEN Implementation

## Огляд

APTEEN (Adaptive Periodic Threshold-sensitive Energy Efficient sensor Network) - це протокол маршрутизації для WSN, що поєднує:
- **LEACH** - кластерну організацію мережі
- **TEEN** - event-driven передачу даних

## Параметри

### LEACH параметри (успадковані)
- `n_cluster: int` - кількість кластерів
- `size_control: int = 128` - розмір керуючих повідомлень (біт)
- `size_data: int = 4096` - розмір пакета даних (біт)
- `energy_agg: float = 5e-9` - енергія агрегації на біт (Дж)
- `agg_rate: float = 0.6` - коефіцієнт стискання при агрегації

### TEEN параметри (нові)

#### `hard_threshold: float = 50.0` (HT)
**Поріг важливості** - мінімальне значення, при якому дозволена передача.

- **Ідея:** "Поки не критично — не передавай"
- Якщо `sensor_value < HT` → не передавати
- Якщо `sensor_value >= HT` → можлива передача (якщо виконані інші умови)

**Приклад:**
```python
# Високий HT - більш суворий (менше передач)
apteen = APTEEN(*nodes, n_cluster=5, hard_threshold=70.0)

# Низький HT - менш суворий (більше передач)
apteen = APTEEN(*nodes, n_cluster=5, hard_threshold=30.0)
```

#### `soft_threshold: float = 2.0` (ST)
**Поріг зміни** - мінімальна зміна значення для повторної передачі.

- **Ідея:** "Не передавай те саме ще раз"
- Якщо `|current_value - last_transmitted| < ST` → не передавати
- Якщо `|current_value - last_transmitted| >= ST` → передати

**Приклад:**
```python
# Високий ST - рідше передавати (лише великі зміни)
apteen = APTEEN(*nodes, n_cluster=5, soft_threshold=10.0)

# Низький ST - частіше передавати (малі зміни теж)
apteen = APTEEN(*nodes, n_cluster=5, soft_threshold=1.0)
```

#### `count_time: int = 10` (TC)
**Періодичне оновлення** - максимум раундів без передачі.

- **Ідея:** "Якщо давно мовчав — дай знати що живий"
- Після TC раундів без передачі → обов'язково передати
- Забезпечує регулярні оновлення навіть без подій

**Приклад:**
```python
# Великий TC - рідкі примусові оновлення
apteen = APTEEN(*nodes, n_cluster=5, count_time=20)

# Малий TC - часті примусові оновлення
apteen = APTEEN(*nodes, n_cluster=5, count_time=5)
```

#### `data_generator: Callable[[Node, int], float] = None`
**Функція генерації даних** для симуляції.

- За замовчуванням використовується `_default_data_generator`
- Можна передати власну функцію для моделювання реальних сенсорів

**Приклад:**
```python
def temperature_sensor(node: Node, round: int) -> float:
    """Симулює температурний сенсор"""
    base_temp = 20.0
    daily_cycle = 5 * sin(2 * pi * round / 24)  # добовий цикл
    noise = random.gauss(0, 1)
    return base_temp + daily_cycle + noise

apteen = APTEEN(*nodes, n_cluster=5, data_generator=temperature_sensor)
```

## Логіка передачі

Вузол передає дані тільки якщо виконані **ВСІ** умови:

```python
def should_transmit(node, current_value):
    # 1. Перевірка важливості
    if current_value < hard_threshold:
        return False  # значення не досить важливе
    
    # 2. Перша передача завжди OK
    if node not in last_transmission:
        return True
    
    # 3. Перевірка зміни
    change = abs(current_value - last_transmission[node])
    if change >= soft_threshold:
        return True  # значна зміна
    
    # 4. Перевірка періоду
    if rounds_since_transmission[node] >= count_time:
        return True  # час для примусового оновлення
    
    return False  # умови не виконані
```

## Приклади використання

### Базовий
```python
from router import APTEEN
from distribution import simple_loader, uniform_in_square

sink = (0, 0)
nodes = simple_loader(sink, uniform_in_square(100, 100, sink))
apteen = APTEEN(*nodes, n_cluster=5)

apteen.initialize()
while len(apteen.alive_non_sinks) > 0:
    apteen.execute()
```

### З налаштуваннями
```python
# Aggressive mode - багато передач
apteen = APTEEN(*nodes, n_cluster=5,
                hard_threshold=40.0,
                soft_threshold=2.0,
                count_time=5)

# Conservative mode - мало передач, економія енергії
apteen = APTEEN(*nodes, n_cluster=5,
                hard_threshold=70.0,
                soft_threshold=10.0,
                count_time=20)
```

### Порівняння
```python
configs = {
    "LEACH": LEACH(*nodes_leach, n_cluster=6),
    "APTEEN-default": APTEEN(*nodes_apt1, n_cluster=6),
    "APTEEN-aggressive": APTEEN(*nodes_apt2, n_cluster=6, 
                                hard_threshold=40.0, soft_threshold=2.0),
}

for name, router in configs.items():
    router.initialize()
    rounds = 0
    while len(router.alive_non_sinks) > 0:
        router.execute()
        rounds += 1
    print(f"{name}: {rounds} rounds")
```

## Переваги APTEEN

1. **Енергоефективність** - передача лише важливих даних
2. **Адаптивність** - реагує на події (HT, ST)
3. **Періодичність** - гарантовані оновлення (TC)
4. **Гнучкість** - налаштування під конкретну задачу

## Різниця між протоколами

| Протокол | Структура | Коли передає | Енергія |
|----------|-----------|--------------|---------|
| LEACH | кластери | завжди | середня |
| TEEN | кластери | лише події | дуже низька |
| APTEEN | кластери | події + періодично | низька |

## Тестування

```bash
# Простий тест
python test_apteen_quick.py

# Повний тест з візуалізацією
python test_apteen.py

# Порівняння протоколів
python compare_leach_and_apteen.py
```

## Внутрішній стан

APTEEN відстежує:
- `last_values[node]` - останнє виміряне значення
- `last_transmission[node]` - останнє передане значення
- `rounds_since_transmission[node]` - раундів з останньої передачі
- `parameters_broadcasted[head]` - чи CH розіслав параметри

## Додаткові методи

### `broadcast_teen_parameters(cluster_head)`
Broadcast HT/ST/TC параметрів від cluster head до членів кластера.
Викликається автоматично в `set_up_phase()`.

```python
# Автоматично викликається при setup
apteen = APTEEN(*nodes, n_cluster=5, hard_threshold=50.0)
apteen.initialize()
apteen.set_up_phase()  # тут відбувається broadcast
```

### `update_parameters_from_query(hard_threshold, soft_threshold, count_time)`
Оновлення параметрів через query від sink (Adaptive частина APTEEN).

```python
# Змінити параметри в runtime
apteen.update_parameters_from_query(
    hard_threshold=30.0,  # знизити важливість
    soft_threshold=5.0,   # підвищити чутливість до змін
    count_time=15         # рідше примусові оновлення
)
# Параметри будуть re-broadcasted на наступному setup
```

### `recursive_gathering_with_teen(head, size)`
Ієрархічний збір даних з TEEN логікою (підтримує multi-hop між CHs).
Використовується в `steady_state_phase()` для hierarchical LEACH (LEACHPrim).

```python
# Викликається автоматично в steady_state
# Підтримує структури де CH можуть бути членами інших CHs
```
