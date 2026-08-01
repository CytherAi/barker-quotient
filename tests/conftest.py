"""Shared fixtures for the barker_k6 test suite."""
import sys
import os

# Make the barker package importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "barker_k6_bundle", "code"))
