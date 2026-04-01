"""
Configuration loader.

Loads config from multiple sources with precedence:
1. Environment variables (highest priority)
2. User config file (~/.tradingagents/config.yaml)
3. Project config file (./config.yaml)
4. Default values (lowest priority)
"""
import os
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_FILE_NAME = "config.yaml"
USER_CONFIG_DIR = Path.home() / ".tradingagents"
PROJECT_CONFIG_PATH = Path(__file__).parent.parent.parent / CONFIG_FILE_NAME


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load YAML config file (without pyyaml dependency)."""
    try:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: parse simple YAML manually
        return _parse_simple_yaml(path)


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse simple YAML (key: value) without pyyaml."""
    result = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Try to parse as number/bool
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.replace(".", "", 1).isdigit():
                    value = float(value) if "." in value else int(value)
                result[key] = value
    return result


def load_json_config(path: Path) -> dict[str, Any]:
    """Load JSON config file."""
    with open(path) as f:
        return json.load(f)


def load_config_file(path: Path) -> dict[str, Any]:
    """Load config file (YAML or JSON)."""
    if not path.exists():
        return {}

    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return load_yaml_config(path)
    elif suffix == ".json":
        return load_json_config(path)
    else:
        logger.warning(f"Unknown config file format: {path}")
        return {}


def get_user_config_path() -> Path | None:
    """Get user config file path if it exists."""
    path = USER_CONFIG_DIR / CONFIG_FILE_NAME
    return path if path.exists() else None


def merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge override into base.

    Args:
        base: Base configuration
        override: Override values (higher priority)

    Returns:
        Merged configuration
    """
    result = base.copy()
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict[str, Any]:
    """
    Load configuration from all sources.

    Precedence (highest to lowest):
    1. Environment variables
    2. User config (~/.tradingagents/config.yaml)
    3. Project config (./config.yaml)
    4. Default values

    Returns:
        Merged configuration dictionary
    """
    from tradingagents_crypto.config.default_config import Config

    # Start with default config
    default = Config()
    result = _dataclass_to_dict(default)

    # Load project config
    if PROJECT_CONFIG_PATH.exists():
        project_config = load_config_file(PROJECT_CONFIG_PATH)
        result = merge_config(result, project_config)
        logger.info(f"Loaded project config from {PROJECT_CONFIG_PATH}")

    # Load user config
    user_path = get_user_config_path()
    if user_path:
        user_config = load_config_file(user_path)
        result = merge_config(result, user_config)
        logger.info(f"Loaded user config from {user_path}")

    # Apply environment variable overrides
    env_overrides = _load_env_overrides()
    if env_overrides:
        result = merge_config(result, env_overrides)
        logger.info("Applied environment variable overrides")

    return result


def _dataclass_to_dict(obj) -> dict[str, Any]:
    """Convert a dataclass to a dict recursively."""
    import dataclasses

    if dataclasses.is_dataclass(obj):
        result = {}
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            result[field.name] = _dataclass_to_dict(value)
        return result
    elif isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    else:
        return obj


def _load_env_overrides() -> dict[str, Any]:
    """Load configuration overrides from environment variables."""
    overrides: dict[str, Any] = {}

    # HL_* env vars
    if os.getenv("HL_USE_TESTNET"):
        overrides.setdefault("hyperliquid", {})["use_testnet"] = (
            os.getenv("HL_USE_TESTNET") == "1"
        )
    if os.getenv("HL_CACHE_TTL"):
        overrides.setdefault("hyperliquid", {})["cache_ttl_seconds"] = int(
            os.getenv("HL_CACHE_TTL")
        )

    # LLM_* env vars
    if os.getenv("LLM_MODEL"):
        overrides.setdefault("llm", {})["model_name"] = os.getenv("LLM_MODEL")
    if os.getenv("LLM_TEMPERATURE"):
        overrides.setdefault("llm", {})["temperature"] = float(
            os.getenv("LLM_TEMPERATURE")
        )

    # TRADING_* env vars
    if os.getenv("TRADING_SYMBOL"):
        overrides.setdefault("trading", {})["default_symbol"] = os.getenv(
            "TRADING_SYMBOL"
        )
    if os.getenv("BACKTEST_MODE"):
        overrides.setdefault("trading", {})["backtest_mode"] = (
            os.getenv("BACKTEST_MODE") == "1"
        )
    if os.getenv("MIN_CONFIDENCE"):
        overrides.setdefault("trading", {})["min_confidence_to_trade"] = float(
            os.getenv("MIN_CONFIDENCE")
        )

    # AGENT_* env vars
    if os.getenv("OUTPUT_LANGUAGE"):
        overrides.setdefault("agent", {})["output_language"] = os.getenv(
            "OUTPUT_LANGUAGE"
        )

    return overrides
