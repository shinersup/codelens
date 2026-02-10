"""
Root conftest.py — sits next to app/ and tests/.

This file runs before ANY test collection happens,
guaranteeing /app is on sys.path before imports.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))