#!/usr/bin/env python3
"""
Демонстрація керування параметрами в APTEEN

Показує як працюють:
1. Глобальні параметри (один HT/ST/TC для всіх)
2. Per-cluster параметри (різні для кожного кластера)
3. Query-based оновлення
"""

from router import APTEEN
from distribution import simple_loader, uniform_in_square
import numpy as np


def demo_global_parameters():
    """1. Глобальні параметри - найпростіший випадок"""
    print("="*70)
    print("1. ГЛОБАЛЬНІ ПАРАМЕТРИ")
    print("="*70)
    print("Всі кластери використовують одні параметри HT/ST/TC\n")
    
    sink = (0, 0)
    nodes = simple_loader(sink, uniform_in_square(100, 12, sink))
    
    # Створюємо з глобальними параметрами
    apteen = APTEEN(*nodes, n_cluster=3, 
                   hard_threshold=50.0,  # HT
                   soft_threshold=2.0,   # ST
                   count_time=10)        # TC
    
    apteen.initialize()
    apteen.set_up_phase()
    
    print(f"Глобальні параметри:")
    print(f"  HT = {apteen.hard_threshold}")
    print(f"  ST = {apteen.soft_threshold}")
    print(f"  TC = {apteen.count_time}\n")
    
    # Перевірка - всі вузли бачать одні параметри
    sample_nodes = list(apteen.alive_non_sinks)[:3]
    for node in sample_nodes:
        ht, st, tc = apteen.get_parameters_for_node(node)
        print(f"Вузол: HT={ht}, ST={st}, TC={tc}")
    
    print("✓ Всі вузли мають однакові параметри\n")


def demo_per_cluster_parameters():
    """2. Різні параметри для різних кластерів - справжня адаптивність"""
    print("="*70)
    print("2. PER-CLUSTER ПАРАМЕТРИ (Адаптивність!)")
    print("="*70)
    print("Різні кластери = різні вимоги = різні параметри\n")
    
    sink = (0, 0)
    nodes = simple_loader(sink, uniform_in_square(100, 15, sink))
    
    apteen = APTEEN(*nodes, n_cluster=3, 
                   hard_threshold=50.0, soft_threshold=2.0, count_time=10)
    
    apteen.initialize()
    apteen.set_up_phase()
    
    # Отримаємо головів кластерів
    cluster_heads = [h for h in apteen.get_cluster_heads() if h != apteen.sink]
    
    # Задамо різні параметри для кожного кластера
    if len(cluster_heads) >= 2:
        # Кластер 1: критична зона (низький HT, малий ST, часті оновлення)
        ch1 = cluster_heads[0]
        apteen.set_cluster_parameters(ch1, 
                                     hard_threshold=30.0,  # нижчий поріг
                                     soft_threshold=1.0,   # чутливіший
                                     count_time=5)         # частіші оновлення
        
        # Кластер 2: некритична зона (високий HT, великий ST, рідкі оновлення)
        ch2 = cluster_heads[1]
        apteen.set_cluster_parameters(ch2,
                                     hard_threshold=70.0,  # вищий поріг
                                     soft_threshold=5.0,   # менш чутливий
                                     count_time=20)        # рідкі оновлення
        
        print("Налаштування кластерів:")
        print(f"\nКластер 1 (критичний):")
        print(f"  HT=30, ST=1, TC=5 → дуже чутливий")
        members1 = list(apteen.get_cluster_members(ch1))[:2]
        for m in members1:
            ht, st, tc = apteen.get_parameters_for_node(m)
            print(f"  Член: HT={ht}, ST={st}, TC={tc}")
        
        print(f"\nКластер 2 (некритичний):")
        print(f"  HT=70, ST=5, TC=20 → економний")
        members2 = list(apteen.get_cluster_members(ch2))[:2]
        for m in members2:
            ht, st, tc = apteen.get_parameters_for_node(m)
            print(f"  Член: HT={ht}, ST={st}, TC={tc}")
        
        if len(cluster_heads) >= 3:
            print(f"\nКластер 3 (default):")
            print(f"  HT=50, ST=2, TC=10 → глобальні параметри")
            ch3 = cluster_heads[2]
            members3 = list(apteen.get_cluster_members(ch3))[:2]
            for m in members3:
                ht, st, tc = apteen.get_parameters_for_node(m)
                print(f"  Член: HT={ht}, ST={st}, TC={tc}")
        
        print("\n✓ Кожен кластер працює за своїми правилами!")


def demo_query_updates():
    """3. Query-based оновлення - sink змінює параметри в runtime"""
    print("\n" + "="*70)
    print("3. QUERY-BASED UPDATES")
    print("="*70)
    print("Sink може змінювати параметри динамічно\n")
    
    sink = (0, 0)
    nodes = simple_loader(sink, uniform_in_square(100, 10, sink))
    
    apteen = APTEEN(*nodes, n_cluster=2,
                   hard_threshold=50.0, soft_threshold=2.0, count_time=10)
    
    apteen.initialize()
    apteen.execute()  # Round 1
    
    print("Round 1:")
    print(f"  Параметри: HT={apteen.hard_threshold}, ST={apteen.soft_threshold}, TC={apteen.count_time}")
    
    # Sink відправляє query для зміни глобальних параметрів
    print("\n⚡ Sink: 'Змінюємо на екстрений режим!'")
    apteen.update_parameters_from_query(
        hard_threshold=20.0,   # дуже низький
        soft_threshold=0.5,    # дуже чутливий
        count_time=3           # дуже часто
    )
    
    print(f"\nRound 2:")
    print(f"  Нові параметри: HT={apteen.hard_threshold}, ST={apteen.soft_threshold}, TC={apteen.count_time}")
    print(f"  Broadcasts очищено: {len(apteen.parameters_broadcasted)} (треба re-broadcast)")
    
    # Execute знову → параметри будуть re-broadcasted
    apteen.execute()
    print(f"  Після execute: {len(apteen.parameters_broadcasted)} CHs broadcasted нові параметри")
    
    print("\n✓ Query дозволяє адаптуватися до ситуації!")


def demo_practical_scenarios():
    """4. Практичні сценарії використання"""
    print("\n" + "="*70)
    print("4. ПРАКТИЧНІ СЦЕНАРІЇ")
    print("="*70)
    
    print("\n📊 Сценарій 1: Моніторинг температури")
    print("   - Нормальна зона: HT=50°C, ST=5°C, TC=20")
    print("   - Біля обладнання: HT=30°C, ST=2°C, TC=5")
    print("   → Критичні зони відправляють більше даних")
    
    print("\n🔋 Сценарій 2: Економія енергії")
    print("   - Вузли з високою батареєю: HT=40, ST=1, TC=10")
    print("   - Вузли з низькою батареєю: HT=70, ST=10, TC=30")
    print("   → Слабкі вузли працюють рідше")
    
    print("\n⚠️ Сценарій 3: Аварійний режим")
    print("   - Звичайний: HT=50, ST=2, TC=10")
    print("   - Query при тривозі: HT=20, ST=0.5, TC=3")
    print("   → Sink отримує максимум інформації")
    
    print("\n🎯 Сценарій 4: Гібридний підхід")
    print("   - 70% кластерів: високі пороги (економія)")
    print("   - 30% кластерів: низькі пороги (якість даних)")
    print("   → Баланс між енергією і точністю")


def summary():
    """Підсумок"""
    print("\n" + "="*70)
    print("ПІДСУМОК: КЕРУВАННЯ ПАРАМЕТРАМИ")
    print("="*70)
    
    print("\n3 рівні керування:")
    print("\n1️⃣  ГЛОБАЛЬНІ параметри")
    print("   apteen = APTEEN(*nodes, hard_threshold=50, ...)")
    print("   → Найпростіший спосіб, всі однакові")
    
    print("\n2️⃣  PER-CLUSTER параметри")
    print("   apteen.set_cluster_parameters(ch, HT, ST, TC)")
    print("   → Кожен кластер унікальний (справжня адаптивність)")
    
    print("\n3️⃣  QUERY оновлення")
    print("   apteen.update_parameters_from_query(HT, ST, TC)")
    print("   → Динамічна зміна в runtime")
    
    print("\n" + "="*70)
    print("КЛЮЧОВА ІДЕЯ:")
    print("  LEACH організує структуру (хто, кому)")
    print("  TEEN визначає логіку (коли передавати)")
    print("  APTEEN додає адаптивність (параметри змінюються)")
    print("="*70 + "\n")


def main():
    np.random.seed(42)
    
    demo_global_parameters()
    demo_per_cluster_parameters()
    demo_query_updates()
    demo_practical_scenarios()
    summary()


if __name__ == "__main__":
    main()
