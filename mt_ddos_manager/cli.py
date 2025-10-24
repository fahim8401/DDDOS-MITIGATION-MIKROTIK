"""
CLI entrypoint for mt-ddos-manager
"""

import click
import logging
from .config import Config
from .db import init_db
from .api import create_app
from .monitor.worker import MonitorWorker
from .tasks import scheduler, cleanup_old_data, backup_database
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
import bcrypt

logging.basicConfig(level=logging.INFO)


@click.group()
def cli():
    """MikroTik DDoS Monitor Manager"""
    pass


@cli.command()
@click.option('--config', default='config.yml', help='Config file path')
def init_db_cmd(config):
    """Initialize database"""
    cfg = Config(config)
    init_db()
    click.echo("Database initialized")


@cli.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('--role', default='admin', type=click.Choice(['admin', 'operator', 'viewer']))
def create_admin(username, password, role):
    """Create admin user"""
    db: Session = next(get_db())

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user = User(
        username=username,
        password_hash=password_hash.decode('utf-8'),
        role=role
    )

    db.add(user)
    db.commit()
    click.echo(f"User {username} created with role {role}")


@cli.command()
@click.option('--config', default='config.yml', help='Config file path')
@click.option('--host', default='0.0.0.0', help='API host')
@click.option('--port', default=5000, help='API port')
def run_api(config, host, port):
    """Run API server"""
    cfg = Config(config)
    app = create_app()

    # Start background tasks
    scheduler.add_task('cleanup', 86400, cleanup_old_data)  # Daily cleanup
    scheduler.add_task('backup', 86400, backup_database)    # Daily backup
    scheduler.start()

    app.run(host=host, port=port, debug=True)


@cli.command()
@click.option('--router-id', required=True, type=int, help='Router ID to monitor')
def monitor_router(router_id):
    """Monitor specific router"""
    worker = MonitorWorker(router_id)
    worker.start()

    try:
        worker.join()
    except KeyboardInterrupt:
        worker.stop()


if __name__ == '__main__':
    cli()