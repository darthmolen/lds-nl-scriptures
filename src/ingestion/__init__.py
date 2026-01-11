"""Ingestion module for Scripture Search project.

Provides utilities and scripts for loading scripture and CFM data into PostgreSQL.

Submodules:
- base: Shared ingestion utilities (CLI parsers, data checks, truncation)

Exports:
- create_scripture_parser: CLI parser factory for scripture ingestion
- check_existing_scriptures: Count existing verses for volume+lang
- truncate_scriptures: Delete verses for volume+lang
- check_or_skip: Check/truncate pattern for scripture ingestion
- create_cfm_parser: CLI parser factory for CFM ingestion
- check_existing_cfm: Count existing CFM lessons for year+lang
- truncate_cfm: Delete CFM lessons for year+lang
- check_or_skip_cfm: Check/truncate pattern for CFM ingestion
- VALID_VOLUMES: Tuple of valid scripture volume names
- VALID_LANGUAGES: Tuple of valid language codes
- VALID_TESTAMENTS: Tuple of valid CFM testament codes
"""

from src.ingestion.base import (
    # Constants
    VALID_LANGUAGES,
    VALID_TESTAMENTS,
    VALID_VOLUMES,
    # CFM utilities
    check_existing_cfm,
    check_or_skip_cfm,
    create_cfm_parser,
    truncate_cfm,
    # Scripture utilities
    check_existing_scriptures,
    check_or_skip,
    create_scripture_parser,
    truncate_scriptures,
)

__all__ = [
    # Constants
    "VALID_VOLUMES",
    "VALID_LANGUAGES",
    "VALID_TESTAMENTS",
    # Scripture utilities
    "create_scripture_parser",
    "check_existing_scriptures",
    "truncate_scriptures",
    "check_or_skip",
    # CFM utilities
    "create_cfm_parser",
    "check_existing_cfm",
    "truncate_cfm",
    "check_or_skip_cfm",
]
