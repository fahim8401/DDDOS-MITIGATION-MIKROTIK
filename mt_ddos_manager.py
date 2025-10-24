#!/usr/bin/env python3
"""
MikroTik DDoS Monitor Multi-Router Manager
Main entry point
"""

import sys
import os

# Add package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mt_ddos_manager.cli import cli

if __name__ == '__main__':
    cli()
