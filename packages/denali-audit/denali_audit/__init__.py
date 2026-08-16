"""denali — the check you run on a hit list before you spend a year on it."""
__version__ = "0.1.0"
from .core import audit, audit_replication          # noqa: F401
from .adapters import detect, SUPPORTED             # noqa: F401
