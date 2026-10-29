#!/usr/bin/env python
"""
AetherAI CLI Entrypoint.
Run `python aether.py` for interactive terminal mode.
Run `python aether.py --help` for command line flags.
"""
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.cli.main import main

if __name__ == "__main__":
    main()
