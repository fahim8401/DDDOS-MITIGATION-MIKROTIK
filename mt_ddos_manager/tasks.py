"""
Background tasks and scheduler
"""

import threading
import time
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from .db import get_db
from .models import Metric, Event

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Background task scheduler"""

    def __init__(self):
        self.tasks = {}
        self.running = True

    def start(self):
        """Start scheduler"""
        threading.Thread(target=self._run_scheduler, daemon=True).start()

    def stop(self):
        """Stop scheduler"""
        self.running = False

    def add_task(self, name: str, interval: int, func, *args, **kwargs):
        """Add recurring task"""
        self.tasks[name] = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'interval': interval,
            'last_run': 0
        }

    def _run_scheduler(self):
        """Run scheduler loop"""
        while self.running:
            current_time = time.time()

            for name, task in self.tasks.items():
                if current_time - task['last_run'] >= task['interval']:
                    try:
                        task['func'](*task['args'], **task['kwargs'])
                        task['last_run'] = current_time
                    except Exception as e:
                        logger.error(f"Error running task {name}: {e}")

            time.sleep(10)  # Check every 10 seconds


def cleanup_old_data(retention_days: int = 30):
    """Clean up old metrics and events"""
    try:
        db: Session = next(get_db())
        cutoff_date = db.func.now() - db.func.interval(retention_days, 'DAY')

        # Delete old metrics
        deleted_metrics = db.query(Metric).filter(Metric.ts < cutoff_date).delete()

        # Delete old events
        deleted_events = db.query(Event).filter(Event.created_at < cutoff_date).delete()

        db.commit()
        logger.info(f"Cleaned up {deleted_metrics} metrics and {deleted_events} events")
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")


def backup_database():
    """Backup database (placeholder)"""
    logger.info("Database backup task (not implemented)")


# Global scheduler instance
scheduler = TaskScheduler()