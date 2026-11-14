"""Public API for mini_html5_named_entity.

Only :func:`decode` and :func:`decode_bytes` are exported. The lookup table
itself lives in :mod:`mini_html5_named_entity.core` and is intentionally not
re-exported: it is large, and callers should not depend on its exact shape.
"""

from .core import decode, decode_bytes

__all__ = ["decode", "decode_bytes"]

__version__ = "1.0.0"
