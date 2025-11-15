"""Adapters for converting CGM-specific formats to normalized format."""

from .base import CGMAdapter
from .dexcom import DexcomAdapter

__all__ = ['CGMAdapter', 'DexcomAdapter']