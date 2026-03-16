"""Pytest conftest: set up sys.path so app modules resolve."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))
