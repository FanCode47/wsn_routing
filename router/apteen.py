from __future__ import annotations

from typing import Callable, Optional
from collections import defaultdict

from router import Node
from router.leach import LEACHPrim


class APTEEN(LEACHPrim):
    """
    APTEEN = LEACH + TEEN
    
    Adaptive Periodic Threshold-sensitive Energy Efficient sensor Network protocol.
    Combines cluster-based routing (LEACH) with event-driven data transmission (TEEN).
    
    Key concepts:
    - Hard Threshold (HT): minimum value to trigger transmission
    - Soft Threshold (ST): minimum change in value to trigger transmission  
    - Count Time (TC): maximum rounds without transmission (periodic update)
    """
    
    def __init__(
        self,
        sink: Node,
        non_sinks,
        *,
        n_cluster: int,
        # LEACH parameters
        size_control: int = 128,
        size_data: int = 4096,
        energy_agg: float = 5e-9,
        agg_rate: float = 0.6,
        # TEEN/APTEEN parameters
        hard_threshold: float = 50.0,
        soft_threshold: float = 2.0,
        count_time: int = 10,
        # Data generation function (for simulation)
        data_generator: Optional[Callable[[Node, int], float]] = None
    ):
        super().__init__(
            sink, non_sinks,
            n_cluster=n_cluster,
            size_control=size_control,
            size_data=size_data,
            energy_agg=energy_agg,
            agg_rate=agg_rate
        )
        
        # TEEN parameters (default/global)
        self.hard_threshold = hard_threshold
        self.soft_threshold = soft_threshold
        self.count_time = count_time
        
        # Per-cluster parameters (adaptive)
        # cluster_parameters[head] = (HT, ST, TC) for this cluster
        self.cluster_parameters: dict[Node, tuple[float, float, int]] = {}
        
        # Data generation
        self.data_generator = data_generator or self._default_data_generator
        
        # State tracking for TEEN logic
        # last_values[node] = last sensed value
        self.last_values: dict[Node, float] = {}
        # last_transmission[node] = last transmitted value
        self.last_transmission: dict[Node, float] = {}
        # rounds_since_transmission[node] = number of rounds since transmission
        self.rounds_since_transmission: dict[Node, int] = defaultdict(int)
        
        # Query/parameter tracking
        # parameters_broadcasted[head] = whether this CH has broadcasted parameters
        self.parameters_broadcasted: dict[Node, bool] = {}
    
    def _default_data_generator(self, node: Node, round: int) -> float:
        """
        Default data generator - simulates sensor readings.
        
        In real scenarios, this would be actual sensor data.
        For simulation, generates values that gradually increase with some noise.
        """
        import numpy as np
        # Base value depends on node position and energy
        base = 30.0 + (node.position[0] + node.position[1]) / 10
        # Add temporal component (increases over time)
        temporal = round * 0.5
        # Add noise
        noise = np.random.normal(0, 5)
        return max(0, base + temporal + noise)
    
    def get_parameters_for_node(self, node: Node) -> tuple[float, float, int]:
        """
        Get parameters (HT, ST, TC) for a specific node.

        If the node belongs to a cluster with custom parameters, return those;
        otherwise return the global defaults.
        """
        # Find the cluster head (CH) for this node
        for head in self.get_cluster_heads():
            if node in self.get_cluster_members(head):
                # If this cluster has custom parameters
                if head in self.cluster_parameters:
                    return self.cluster_parameters[head]
                break
        
        # Global default parameters
        return (self.hard_threshold, self.soft_threshold, self.count_time)
    
    def should_transmit(self, node: Node, current_value: float) -> bool:
        """
        TEEN decision logic: should this node transmit?
        
        Transmission occurs if:
        1. current_value >= hard_threshold AND
        2. (|current_value - last_transmission| >= soft_threshold OR
           rounds_since_transmission >= count_time)
        
        Uses per-cluster parameters if available.
        """
        # Get parameters for this specific node
        hard_threshold, soft_threshold, count_time = self.get_parameters_for_node(node)
        
        # First check: is value important enough?
        if current_value < hard_threshold:
            return False
        
        # If never transmitted, transmit now
        if node not in self.last_transmission:
            return True
        
        # Check if change is significant
        change = abs(current_value - self.last_transmission[node])
        if change >= soft_threshold:
            return True
        
        # Check if too long since last transmission (periodic update)
        if self.rounds_since_transmission[node] >= count_time:
            return True
        
        return False
    
    def broadcast_teen_parameters(self, cluster_head: Node):
        """
        Broadcast TEEN parameters (HT, ST, TC) from cluster head to members.
        
        In APTEEN, each CH sends these thresholds to its cluster members
        after the cluster setup phase. This allows members to make local
        transmission decisions.
        """
        members = self.get_cluster_members(cluster_head)
        if members:
            # Get parameters for this cluster (custom or global)
            if cluster_head in self.cluster_parameters:
                ht, st, tc = self.cluster_parameters[cluster_head]
            else:
                ht, st, tc = self.hard_threshold, self.soft_threshold, self.count_time
            
            # Broadcast parameters to all cluster members
            # Size includes: HT (float), ST (float), TC (int) ≈ 20 bytes control message
            for member in members:
                if member.is_alive():
                    member.recv_broadcast(self.size_control)
            
            # CH spends energy for broadcast
            cluster_head.broadcast(self.size_control, len(members))
            self.parameters_broadcasted[cluster_head] = True
    
    def set_cluster_parameters(self, cluster_head: Node, 
                               hard_threshold: float, 
                               soft_threshold: float, 
                               count_time: int):
        """
        Set custom parameters for a specific cluster.

        This lets different clusters run with different thresholds
        (true APTEEN adaptability).

        Args:
            cluster_head: Cluster head node
            hard_threshold: HT for this cluster
            soft_threshold: ST for this cluster
            count_time: TC for this cluster
        """
        self.cluster_parameters[cluster_head] = (hard_threshold, soft_threshold, count_time)
        # Mark that this CH needs to re-broadcast
        if cluster_head in self.parameters_broadcasted:
            del self.parameters_broadcasted[cluster_head]
    
    def update_parameters_from_query(self, hard_threshold: float = None, 
                                     soft_threshold: float = None, 
                                     count_time: int = None):
        """
        Update TEEN parameters based on query from sink.
        
        This implements the "Adaptive" part of APTEEN - the sink can
        adjust thresholds based on observed network behavior.
        
        Args:
            hard_threshold: New HT value (if provided)
            soft_threshold: New ST value (if provided)
            count_time: New TC value (if provided)
        """
        if hard_threshold is not None:
            self.hard_threshold = hard_threshold
        if soft_threshold is not None:
            self.soft_threshold = soft_threshold
        if count_time is not None:
            self.count_time = count_time
        
        # Mark that parameters need to be re-broadcasted
        self.parameters_broadcasted.clear()
        
        # Sink broadcasts query to all CHs (simplified: assume all CHs receive)
        for head in self.get_cluster_heads():
            if head != self.sink and head.is_alive():
                head.recv_broadcast(self.size_control)
    
    def set_up_phase(self):
        """
        Override setup phase to add TEEN parameter broadcast.
        
        After forming clusters (via LEACH), each CH broadcasts
        HT, ST, TC to its members.
        """
        # Call parent's setup (clustering)
        super().set_up_phase()
        
        # Broadcast TEEN parameters from each CH to members
        for head in self.get_cluster_heads():
            if head != self.sink and head.is_alive():
                self.broadcast_teen_parameters(head)
    
    def steady_state_phase(self):
        """
        APTEEN steady state: event-driven + periodic data transmission with TDMA.
        
        Override LEACH's steady_state_phase to add TEEN logic.
        Implements TDMA schedule where nodes may skip their slots if 
        TEEN conditions are not met (empty slots).
        
        Uses hierarchical gathering for LEACHPrim (multi-hop between CHs).
        """
        if not self.clusters:
            return
        
        # Sense data at all nodes
        for node in self.alive_non_sinks:
            current_value = self.data_generator(node, self.round)
            self.last_values[node] = current_value
            self.rounds_since_transmission[node] += 1
        
        # Use hierarchical recursive gathering (supports multi-hop CHs)
        self.recursive_gathering_with_teen(self.sink, self.size_data)
    
    def recursive_gathering_with_teen(self, head: Node, size: int) -> tuple[int, bool]:
        """
        Modified recursive gathering with TEEN logic.
        
        Returns:
            tuple[int, bool]: (aggregated_size, has_data)
                - aggregated_size: total size after aggregation
                - has_data: whether any data was transmitted
        """
        members = self.get_cluster_members(head)
        size_agg = 0
        size_not_agg = size if head != self.sink else 0
        has_any_data = False
        
        for member in members:
            if not member.is_alive():
                continue
                
            if self.is_cluster_head(member):
                # Recursive call for cluster heads
                size_sub, has_data = self.recursive_gathering_with_teen(member, size)
                if has_data:
                    member.singlecast(size_sub, head)
                    size_agg += size_sub
                    has_any_data = True
            else:
                # Regular cluster member - check TEEN conditions
                if member in self.last_values:
                    current_value = self.last_values[member]
                    
                    if self.should_transmit(member, current_value):
                        # Transmit data
                        member.singlecast(size, head)
                        size_not_agg += size
                        has_any_data = True
                        
                        # Update transmission tracking
                        self.last_transmission[member] = current_value
                        self.rounds_since_transmission[member] = 0
        
        # Aggregate if we have data
        if has_any_data or size_not_agg > 0:
            aggregated = self.aggregation(head, size_not_agg) + size_agg
            return aggregated, True
        
        return 0, False
