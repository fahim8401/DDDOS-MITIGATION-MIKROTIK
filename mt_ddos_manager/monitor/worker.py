"""
Monitor worker for individual routers
"""

import threading
import time
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Router, RouterConfig, Metric, Event, ActionHistory
from .router_client import RouterClient
from .monitor import Monitor
import json

logger = logging.getLogger(__name__)


class MonitorWorker(threading.Thread):
    """Worker thread for monitoring a single router"""

    def __init__(self, router_id: int, shared_queue=None):
        super().__init__(daemon=True)
        self.router_id = router_id
        self.shared_queue = shared_queue
        self.running = True
        self.client = None
        self.monitor = None
        self.config = None

    def run(self):
        """Main worker loop"""
        logger.info(f"Starting monitor worker for router {self.router_id}")

        while self.running:
            try:
                # Load router config
                db: Session = next(get_db())
                router = db.query(Router).filter(Router.id == self.router_id).first()
                if not router or not router.enabled:
                    time.sleep(30)  # Wait before checking again
                    continue

                config = db.query(RouterConfig).filter(RouterConfig.router_id == self.router_id).first()
                if not config:
                    logger.warning(f"No config found for router {self.router_id}")
                    time.sleep(30)
                    continue

                self.config = config

                # Initialize client and monitor if needed
                if not self.client:
                    self.client = RouterClient(
                        host=router.host,
                        username=router.username,
                        password=router.password,
                        port=router.port,
                        use_ssl=router.use_ssl
                    )

                if not self.monitor:
                    thresholds = {
                        'conn_attack_threshold': config.conn_attack_threshold or 10000,
                        'new_conn_rate_threshold': config.new_conn_rate_threshold or 1000,
                        'packet_threshold': 100000
                    }
                    self.monitor = Monitor(thresholds)

                # Poll router
                self._poll_router(router, config, db)

                # Update last seen
                router.last_seen = db.func.now()
                db.commit()

            except Exception as e:
                logger.error(f"Error in monitor worker for router {self.router_id}: {e}")

            # Wait for next poll
            time.sleep(self.config.poll_interval or 30)

    def stop(self):
        """Stop the worker"""
        self.running = False
        if self.client:
            self.client.disconnect()

    def _poll_router(self, router: Router, config: RouterConfig, db: Session):
        """Poll the router for metrics and detect attacks"""
        try:
            # Get current metrics
            conn_count = self.client.get_total_connections_count()
            interface_stats = self.client.monitor_interface_traffic('ether1')  # Assuming ether1

            # Calculate deltas (simplified - in real implementation, track previous values)
            new_conn_delta = 0  # Would need to track previous conn_count

            # Create metric record
            metric = Metric(
                router_id=router.id,
                total_connections=conn_count,
                new_connections=new_conn_delta,
                packets_in=interface_stats.get('rx-packets-per-second', 0),
                packets_out=interface_stats.get('tx-packets-per-second', 0),
                bytes_in=interface_stats.get('rx-bits-per-second', 0) // 8,
                bytes_out=interface_stats.get('tx-bits-per-second', 0) // 8
            )
            db.add(metric)

            # Detect attacks
            current_state = {
                'total_connections': conn_count,
                'new_connections_delta': new_conn_delta,
                'interface_stats': interface_stats
            }
            result = self.monitor.detect_attack(current_state)

            if result.action != 'none':
                # Create event
                event = Event(
                    router_id=router.id,
                    type='attack_detected',
                    detail=result.reason,
                    meta=json.dumps({
                        'action': result.action,
                        'attackers': result.attackers,
                        'targets': result.targets
                    }),
                    severity='high'
                )
                db.add(event)

                # Execute action
                self._execute_action(result.action, router, db)

            db.commit()

        except Exception as e:
            logger.error(f"Error polling router {router.id}: {e}")

    def _execute_action(self, action: str, router: Router, db: Session):
        """Execute mitigation action"""
        try:
            if action == 'tighten':
                # Run tighten script
                result = self.client.run_script('ddos-tighten')
                if result['success']:
                    # Log action
                    history = ActionHistory(
                        router_id=router.id,
                        action='tighten',
                        detail='Automatic tighten due to attack detection'
                    )
                    db.add(history)
                    logger.info(f"Tightened security on router {router.id}")
            elif action == 'restore':
                # Run restore script
                result = self.client.run_script('ddos-restore')
                if result['success']:
                    history = ActionHistory(
                        router_id=router.id,
                        action='restore',
                        detail='Automatic restore to normal'
                    )
                    db.add(history)
                    logger.info(f"Restored normal security on router {router.id}")
        except Exception as e:
            logger.error(f"Error executing action {action} on router {router.id}: {e}")