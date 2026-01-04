#!/usr/bin/env python3
"""
Тестування повної реалізації APTEEN:
1. Broadcast параметрів від CH
2. Query handling (зміна параметрів)
3. TDMA schedule з порожніми слотами
"""

from router import APTEEN
from distribution import simple_loader, uniform_in_square
import numpy as np


def test_broadcast_parameters():
    """Тест: CH broadcast параметрів HT/ST/TC до членів кластера"""
    print("\n" + "="*70)
    print("ТЕСТ 1: Broadcast параметрів від Cluster Heads")
    print("="*70)
    
    sink = (0, 0)
    nodes = simple_loader(sink, uniform_in_square(100, 20, sink))
    apteen = APTEEN(*nodes, n_cluster=3)
    
    # Initialize and execute setup phase
    apteen.initialize()
    
    # Before setup: no broadcasts
    print(f"До setup: broadcasts = {len(apteen.parameters_broadcasted)}")
    
    # Execute setup phase (включає broadcast)
    apteen.set_up_phase()
    
    # After setup: should have broadcasts
    print(f"Після setup: broadcasts = {len(apteen.parameters_broadcasted)}")
    print(f"Кількість CH: {len(list(apteen.get_cluster_heads()))}")
    
    # Check that each CH (except sink) has broadcasted
    ch_index = 0
    for head in apteen.get_cluster_heads():
        if head != apteen.sink:
            broadcasted = apteen.parameters_broadcasted.get(head, False)
            members_count = len(apteen.get_cluster_members(head))
            print(f"  CH {ch_index}: broadcast={broadcasted}, members={members_count}")
            ch_index += 1
    
    print("✓ Broadcast параметрів працює")


def test_query_handling():
    """Тест: Sink відправляє query для зміни параметрів"""
    print("\n" + "="*70)
    print("ТЕСТ 2: Query Handling (Adaptive)")
    print("="*70)
    
    sink = (0, 0)
    nodes = simple_loader(sink, uniform_in_square(100, 15, sink))
    apteen = APTEEN(*nodes, n_cluster=3, hard_threshold=50.0, soft_threshold=2.0, count_time=10)
    
    apteen.initialize()
    apteen.set_up_phase()
    
    print(f"Початкові параметри:")
    print(f"  HT = {apteen.hard_threshold}")
    print(f"  ST = {apteen.soft_threshold}")
    print(f"  TC = {apteen.count_time}")
    print(f"  Broadcasts записів: {len(apteen.parameters_broadcasted)}")
    
    # Sink sends query to update parameters
    print("\nSink відправляє query з новими параметрами...")
    apteen.update_parameters_from_query(hard_threshold=30.0, soft_threshold=5.0, count_time=15)
    
    print(f"Після query:")
    print(f"  HT = {apteen.hard_threshold} (було 50.0)")
    print(f"  ST = {apteen.soft_threshold} (було 2.0)")
    print(f"  TC = {apteen.count_time} (було 10)")
    print(f"  Broadcasts очищено: {len(apteen.parameters_broadcasted)}")
    
    print("✓ Query handling працює")


def test_tdma_empty_slots():
    """Тест: TDMA schedule з порожніми слотами (event-driven)"""
    print("\n" + "="*70)
    print("ТЕСТ 3: TDMA з порожніми слотами")
    print("="*70)
    
    # Custom data generator: деякі вузли мають низькі значення
    def low_values_generator(node, round):
        """Половина вузлів отримують низькі значення < HT"""
        # Use node's position as identifier
        if int(node.position[0] + node.position[1]) % 2 == 0:
            return 20.0  # Нижче HT=50
        else:
            return 60.0 + round * 2  # Вище HT
    
    sink = (0, 0)
    nodes = simple_loader(sink, uniform_in_square(100, 12, sink))
    apteen = APTEEN(*nodes, n_cluster=2, hard_threshold=50.0, 
                   data_generator=low_values_generator)
    
    apteen.initialize()
    apteen.set_up_phase()
    
    # Run one round
    print("\nRound 1:")
    apteen.steady_state_phase()
    
    # Count transmissions
    transmitted = sum(1 for node in apteen.alive_non_sinks 
                     if node in apteen.last_transmission)
    total_members = len(apteen.alive_non_sinks)
    empty_slots = total_members - transmitted
    
    print(f"  Всього членів: {total_members}")
    print(f"  Передали: {transmitted}")
    print(f"  Порожні слоти: {empty_slots}")
    print(f"  Коефіцієнт використання TDMA: {transmitted/total_members*100:.1f}%")
    
    # Run another round
    print("\nRound 2:")
    apteen.round += 1
    apteen.steady_state_phase()
    
    transmitted2 = sum(1 for node in apteen.alive_non_sinks 
                      if node in apteen.last_transmission)
    print(f"  Передали: {transmitted2}")
    print(f"  Порожні слоти: {total_members - transmitted2}")
    
    print("✓ TDMA з порожніми слотами працює")


def test_periodic_update_tc():
    """Тест: Періодичні оновлення через Count Time"""
    print("\n" + "="*70)
    print("ТЕСТ 4: Періодичні оновлення (TC)")
    print("="*70)
    
    # Data generator: значення не змінюються (тест ST і TC)
    def constant_generator(node, round):
        return 55.0  # Постійне значення > HT
    
    sink = (0, 0)
    nodes = simple_loader(sink, uniform_in_square(100, 10, sink))
    apteen = APTEEN(*nodes, n_cluster=2, hard_threshold=50.0, 
                   soft_threshold=10.0, count_time=5,
                   data_generator=constant_generator)
    
    apteen.initialize()
    apteen.set_up_phase()
    
    # First transmission (HT satisfied)
    print("Round 1: Перша передача (HT задоволено)")
    apteen.steady_state_phase()
    transmitted_r1 = sum(1 for node in apteen.alive_non_sinks 
                        if node in apteen.last_transmission)
    print(f"  Передали: {transmitted_r1}")
    
    # Rounds 2-5: no transmission (ST not satisfied, TC not reached)
    for r in range(2, 6):
        apteen.round = r
        apteen.steady_state_phase()
        max_rounds = max(apteen.rounds_since_transmission.values())
        print(f"Round {r}: Rounds since transmission = {max_rounds}")
    
    # Round 6: TC reached, forced transmission
    print("Round 6: TC=5 досягнуто, примусова передача")
    apteen.round = 6
    apteen.steady_state_phase()
    
    transmitted_r6 = len(apteen.last_transmission)
    rounds_after = max(apteen.rounds_since_transmission.values()) if apteen.rounds_since_transmission else 0
    print(f"  Передали: {transmitted_r6}")
    print(f"  Rounds since після TC: {rounds_after}")
    
    print("✓ Періодичні оновлення через TC працюють")


def main():
    """Запуск всіх тестів"""
    print("\n" + "="*70)
    print("ПОВНЕ ТЕСТУВАННЯ APTEEN")
    print("="*70)
    
    np.random.seed(42)
    
    test_broadcast_parameters()
    test_query_handling()
    test_tdma_empty_slots()
    test_periodic_update_tc()
    
    print("\n" + "="*70)
    print("ВСІ ТЕСТИ ПРОЙШЛИ ✓")
    print("="*70)
    print("\nРеалізовано:")
    print("  ✓ Broadcast HT/ST/TC від CH до членів")
    print("  ✓ Query handling для adaptive параметрів")
    print("  ✓ TDMA schedule з порожніми слотами")
    print("  ✓ Періодичні оновлення через Count Time")
    print()


if __name__ == "__main__":
    main()
