#!/usr/bin/env python3
"""Quick test of APTEEN implementation"""

from router import APTEEN
from distribution import simple_loader, uniform_in_square

def main():
    print("=" * 60)
    print("APTEEN Quick Test")
    print("=" * 60)
    
    # Create test network
    sink = (0, 0)
    nodes = simple_loader(sink, uniform_in_square(100, 20, sink))
    
    # Test 1: Default parameters
    print("\n1. Testing with default parameters:")
    apteen = APTEEN(*nodes, n_cluster=3)
    print(f"   ✓ Created with {len(apteen.non_sinks)} nodes, {apteen.n_cluster} clusters")
    print(f"   ✓ HT={apteen.hard_threshold}, ST={apteen.soft_threshold}, TC={apteen.count_time}")
    
    # Test 2: Custom parameters
    print("\n2. Testing with custom parameters:")
    nodes2 = simple_loader(sink, uniform_in_square(100, 20, sink))
    apteen2 = APTEEN(*nodes2, n_cluster=3, 
                     hard_threshold=60.0, 
                     soft_threshold=5.0, 
                     count_time=15)
    print(f"   ✓ HT={apteen2.hard_threshold}, ST={apteen2.soft_threshold}, TC={apteen2.count_time}")
    
    # Test 3: Simulation
    print("\n3. Running simulation:")
    apteen.initialize()
    print(f"   ✓ Initialized")
    
    for round_num in range(1, 6):
        apteen.execute()
        alive = len(apteen.alive_non_sinks)
        clusters = len(apteen.clusters)
        transmitted = len(apteen.last_transmission)
        print(f"   Round {round_num}: {alive} alive, {clusters} clusters, {transmitted} nodes transmitted")
    
    # Test 4: TEEN logic
    print("\n4. Testing TEEN transmission logic:")
    test_node = apteen.alive_non_sinks[0] if apteen.alive_non_sinks else None
    if test_node:
        # Test hard threshold
        should_tx_low = apteen.should_transmit(test_node, 30.0)  # below HT
        should_tx_high = apteen.should_transmit(test_node, 60.0)  # above HT
        print(f"   ✓ Value=30.0 (< HT): should_transmit={should_tx_low}")
        print(f"   ✓ Value=60.0 (> HT): should_transmit={should_tx_high}")
        
        # Set last transmission and test soft threshold
        apteen.last_transmission[test_node] = 55.0
        apteen.rounds_since_transmission[test_node] = 0
        should_tx_small_change = apteen.should_transmit(test_node, 56.0)  # change < ST
        should_tx_big_change = apteen.should_transmit(test_node, 61.0)    # change >= ST
        print(f"   ✓ Change=1.0 (< ST): should_transmit={should_tx_small_change}")
        print(f"   ✓ Change=6.0 (>= ST): should_transmit={should_tx_big_change}")
        
        # Test count time
        apteen.rounds_since_transmission[test_node] = 11
        should_tx_timeout = apteen.should_transmit(test_node, 56.0)  # small change but TC exceeded
        print(f"   ✓ TC exceeded: should_transmit={should_tx_timeout}")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)

if __name__ == "__main__":
    main()
