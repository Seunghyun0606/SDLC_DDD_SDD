#!/usr/bin/env python3
"""Deprecated v1.9 compatibility wrapper.

The canonical control-plane resolver is ``project_config.py``.  This module intentionally owns no
Business/Runtime rule so version-specific config implementations cannot drift.  Existing imports
remain valid during migration.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("project_config_current", HERE / "project_config.py")
CURRENT = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(CURRENT)

PROJECT_ENTRY_PATH = CURRENT.PROJECT_ENTRY_PATH
LEGACY_PROJECT_PROFILE_PATH = CURRENT.LEGACY_PROJECT_PROFILE_PATH
LEGACY_SOURCE_PROFILE_PATH = CURRENT.LEGACY_SOURCE_PROFILE_PATH
DEFAULT_PROVIDER_CONFIG_PATH = CURRENT.DEFAULT_PROVIDER_CONFIG_PATH
EFFECTIVE_DIR = CURRENT.EFFECTIVE_DIR
DELIVERY_PROFILES = CURRENT.DELIVERY_PROFILES
AGENT_EXECUTION_MODES = CURRENT.AGENT_EXECUTION_MODES
DEFAULT_ENGINEERING_PROFILE = CURRENT.DEFAULT_ENGINEERING_PROFILE
DEFAULT_CUSTOMER_PROFILE = CURRENT.DEFAULT_CUSTOMER_PROFILE
DEFAULT_PM_PROFILE = CURRENT.DEFAULT_PM_PROFILE

load_yaml_subset = CURRENT.load_yaml_subset
load_config = CURRENT.load_config
nested = CURRENT.nested
project_mode = CURRENT.project_mode
delivery_profile = CURRENT.delivery_profile
delivery_policy = CURRENT.delivery_policy
command_list = CURRENT.command_list
provider_command = CURRENT.provider_command
agent_execution_mode = CURRENT.agent_execution_mode
resolve_agent_runtime = CURRENT.resolve_agent_runtime
source_roots = CURRENT.source_roots
build_commands = CURRENT.build_commands
test_commands = CURRENT.test_commands
legacy_to_project = CURRENT.legacy_to_project
normalize_document_profiles = CURRENT.normalize_document_profiles
classify_project_config = CURRENT.classify_project_config
ensure_no_dead_config = CURRENT.ensure_no_dead_config
compact_project_context = CURRENT.compact_project_context
project_to_legacy_profiles = CURRENT.project_to_legacy_profiles
resolve_runtime_config = CURRENT.resolve_runtime_config
materialize_effective_profiles = CURRENT.materialize_effective_profiles
