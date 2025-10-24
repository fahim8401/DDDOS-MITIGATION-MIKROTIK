#!/usr/bin/env python3
"""
Import RouterOS scripts to a router
"""

import sys
import click
from sqlalchemy.orm import Session

# Add package to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mt_ddos_manager.db import get_db
from mt_ddos_manager.models import Router
from mt_ddos_manager.monitor.router_client import RouterClient


@click.command()
@click.option('--router-id', required=True, type=int, help='Router ID')
@click.option('--rsc-file', default='../mikrotik-scripts.rsc', help='RSC file path')
def import_rsc(router_id, rsc_file):
    """Import RSC file to router"""
    db: Session = next(get_db())

    router = db.query(Router).filter(Router.id == router_id).first()
    if not router:
        click.echo(f"Router with ID {router_id} not found")
        return

    # Read RSC file
    try:
        with open(rsc_file, 'r') as f:
            rsc_content = f.read()
    except FileNotFoundError:
        click.echo(f"RSC file {rsc_file} not found")
        return

    # Connect to router
    client = RouterClient(
        host=router.host,
        username=router.username,
        password=router.password,
        port=router.port,
        use_ssl=router.use_ssl
    )

    try:
        client.connect()
        # Note: In real implementation, you'd need to upload and import the RSC
        # This is a placeholder
        click.echo(f"RSC import to router '{router.name}' completed (placeholder)")
    except Exception as e:
        click.echo(f"Failed to import RSC: {e}")
    finally:
        client.disconnect()


if __name__ == '__main__':
    import_rsc()