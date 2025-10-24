#!/usr/bin/env python3
"""
CLI tool to add a router to the database
"""

import sys
import click
from sqlalchemy.orm import Session

# Add package to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mt_ddos_manager.db import get_db
from mt_ddos_manager.models import Router, RouterConfig


@click.command()
@click.option('--name', required=True, help='Router name')
@click.option('--host', required=True, help='Router host/IP')
@click.option('--port', default=8728, help='Router port')
@click.option('--username', required=True, help='Router username')
@click.option('--password', required=True, help='Router password')
@click.option('--use-ssl', default=False, is_flag=True, help='Use SSL')
@click.option('--tags', default='', help='Comma-separated tags')
def add_router(name, host, port, username, password, use_ssl, tags):
    """Add a router to the database"""
    db: Session = next(get_db())

    # Check if router exists
    existing = db.query(Router).filter(Router.name == name).first()
    if existing:
        click.echo(f"Router '{name}' already exists")
        return

    # Create router
    router = Router(
        name=name,
        host=host,
        port=port,
        username=username,
        password=password,
        use_ssl=use_ssl,
        tags=tags
    )

    db.add(router)
    db.commit()
    db.refresh(router)

    # Create default config
    config = RouterConfig(router_id=router.id)
    db.add(config)
    db.commit()

    click.echo(f"Router '{name}' added with ID {router.id}")


if __name__ == '__main__':
    add_router()