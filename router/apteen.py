from __future__ import annotations

from typing import Iterable
import random

from router.leach import LEACHPrim
from router.node import Node


class APTEEN(LEACHPrim):
    """Minimal APTEEN implementation (prototype).

    Behavior:
    - Inherits cluster formation and routing from LEACHPrim.
    - Periodic full-data collection every `period` rounds (like LEACH).
    - Event-driven (threshold-free) immediate transmissions: each
      alive sensor may generate an event with probability `event_prob`
      in a round and send a small control/event message to its
      cluster head.

    This is a lightweight prototype to explore APTEEN-style behavior.
    """

    def __init__(
            self,
            sink: Node,
            non_sinks: Iterable[Node],
            *,
            period: int = 10,
            event_prob: float = 0.01,
            event_size: int | None = None,
            **kwargs,
    ):
        super().__init__(sink, non_sinks, **kwargs)
        # period (in rounds) for periodic reporting
        self.period = max(1, int(period))
        # probability that a sensor generates an event in a round
        self.event_prob = float(event_prob)
        # size of event messages (bits); default to control message size
        self.event_size = event_size if event_size is not None else self.size_control
        # threshold parameters (values in [0,1] representing normalized sensor reading)
        self.hard_threshold: float | None = None
        self.soft_threshold: float | None = None
        self.soft_delta: float = 0.1  # minimum change to trigger soft-threshold event
        # minimum rounds between reports from same node for soft-threshold
        self.min_report_interval: int = 1

        # per-node sampling state for threshold logic
        self._last_sample: dict[Node, float] = {node: 0.0 for node in self.non_sinks}
        self._last_report_round: dict[Node, int] = {node: -9999 for node in self.non_sinks}
        # last reported value per node (used for soft-threshold comparisons)
        self._last_report_value: dict[Node, float] = {node: 0.0 for node in self.non_sinks}

    def steady_state_phase(self):
        """Perform periodic aggregation and handle event-driven reports.

        Periodic: every `self.period` rounds perform a full recursive
        gathering (data aggregation) as in LEACH.

        Event-driven: each alive non-sink may generate an event with
        probability `self.event_prob` and send an event message to its
        cluster head (or sink if no head assigned).
        """
        # Periodic collection (full data reports)
        if (self.round % self.period) == 0:
            # sample nodes before periodic gathering to simulate readings
            for node in list(self.alive_non_sinks):
                self._last_sample[node] = random.random()
            # gather application data bits
            self.recursive_gathering(self.sink, self.size_data)
            # after periodic reporting, update last_report_value to suppress immediate duplicate events
            for node in list(self.alive_non_sinks):
                self._last_report_value[node] = self._last_sample.get(node, 0.0)

        # Event-driven tiny reports (immediate, smaller messages)
        # Iterate over a snapshot of alive nodes
        candidates = list(self.alive_non_sinks)
        for node in candidates:
            if not node.is_alive():
                continue
            # simulate a sensor reading in [0,1]
            sample = random.random()
            last = self._last_sample.get(node, 0.0)
            self._last_sample[node] = sample

            # Hard threshold: immediate report if exceeded
            reported = False
            if self.hard_threshold is not None and sample >= self.hard_threshold:
                dst = self.node(self.route[self.index(node)])
                node.singlecast(self.event_size, dst)
                self._last_report_round[node] = self.round
                self._last_report_value[node] = sample
                reported = True

            # Soft threshold: report if above soft threshold AND change >= soft_delta
            if (not reported) and (self.soft_threshold is not None):
                if sample >= self.soft_threshold and abs(sample - last) >= self.soft_delta:
                    if (self.round - self._last_report_round.get(node, -9999)) >= self.min_report_interval:
                        dst = self.node(self.route[self.index(node)])
                        node.singlecast(self.event_size, dst)
                        self._last_report_round[node] = self.round
                        self._last_report_value[node] = sample
                        reported = True

            # Probabilistic events (fallback) if thresholds not set
            if (not reported) and (random.random() < self.event_prob):
                dst = self.node(self.route[self.index(node)])
                node.singlecast(self.event_size, dst)
                self._last_report_value[node] = sample

