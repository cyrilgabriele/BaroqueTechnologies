"""Load and normalise YAML config for index panel cleaning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONFIG_PATH = REPO_ROOT / "baroque" / "src" / "config" / "data" / "indices.yaml"


@dataclass(frozen=True)
class DataCleaningConfig:
    input_dir: Path
    output_path: Path
    symbols: tuple[str, ...]
    required_columns: tuple[str, ...]
    float_columns: tuple[str, ...]
    integer_columns: tuple[str, ...]
    max_allowed_calendar_gap_days: int
    max_isolated_edge_rows: int


def _resolve_repo_path(path_value: str) -> Path:
    return REPO_ROOT / path_value


def load_data_cleaning_config(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> DataCleaningConfig:
    with config_path.open(encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file)

    cleaning = raw_config["cleaning"]

    return DataCleaningConfig(
        input_dir=_resolve_repo_path(str(cleaning["input_dir"])),
        output_path=_resolve_repo_path(str(cleaning["output_path"])),
        symbols=tuple(str(symbol).upper() for symbol in cleaning["symbols"]),
        required_columns=tuple(str(column) for column in cleaning["required_columns"]),
        float_columns=tuple(str(column) for column in cleaning["float_columns"]),
        integer_columns=tuple(str(column) for column in cleaning["integer_columns"]),
        max_allowed_calendar_gap_days=int(cleaning["max_allowed_calendar_gap_days"]),
        max_isolated_edge_rows=int(cleaning["max_isolated_edge_rows"]),
    )
