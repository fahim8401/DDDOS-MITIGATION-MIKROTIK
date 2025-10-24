"""
Monitor logic for DDoS detection
Unit-testable detection algorithms
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """Result of attack detection"""
    action: str  # 'none', 'tighten', 'restore', 'blacklist'
    reason: str
    attackers: List[str]
    targets: List[str]


class Monitor:
    """DDoS detection logic"""

    def __init__(self, thresholds: Dict[str, Any]):
        self.thresholds = thresholds

    def sample(self, conn_count: int, new_conn_delta: int, interface_stats: Dict[str, Any]) -> DetectionResult:
        """Sample current state and detect attacks"""
        # Simple detection logic - can be extended
        action = 'none'
        reason = 'Normal traffic'
        attackers = []
        targets = []

        # Check connection thresholds
        if conn_count > self.thresholds.get('conn_attack_threshold', 10000):
            action = 'tighten'
            reason = f'High connection count: {conn_count}'
        elif new_conn_delta > self.thresholds.get('new_conn_rate_threshold', 1000):
            action = 'tighten'
            reason = f'High new connection rate: {new_conn_delta}'

        # Check packet rates
        packets_in = interface_stats.get('rx-packets-per-second', 0)
        if packets_in > self.thresholds.get('packet_threshold', 100000):
            action = 'tighten'
            reason = f'High packet rate: {packets_in} packets/sec'

        return DetectionResult(
            action=action,
            reason=reason,
            attackers=attackers,
            targets=targets
        )

    def detect_attack(self, current_state: Dict[str, Any]) -> DetectionResult:
        """Main detection method"""
        conn_count = current_state.get('total_connections', 0)
        new_conn_delta = current_state.get('new_connections_delta', 0)
        interface_stats = current_state.get('interface_stats', {})

        return self.sample(conn_count, new_conn_delta, interface_stats)