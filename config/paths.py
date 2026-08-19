"""Shared filesystem paths used by configuration and storage modules."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "config" / "prompts"
STORAGE_DIR = PROJECT_ROOT / "storage"

CASE_LOG_PATH = STORAGE_DIR / "case_log.jsonl"
AUDIT_LOG_PATH = STORAGE_DIR / "audit_log.jsonl"
EMERGENCY_NUMBERS_PATH = STORAGE_DIR / "emergency_numbers.json"
