"""Build the BTC RSI/ATR strategy feature panel from a cleaned panel."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict
import yaml


def find_repo_root(start: Path) -> Path:
    for path in (start, *start.parents):
        if (path / "baroque" / "src" / "config").exists():
            return path

    raise RuntimeError("Could not locate repository root from strategy script path.")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
DEFAULT_CONFIG_PATH = (
    REPO_ROOT
    / "baroque"
    / "src"
    / "config"
    / "strategies"
    / "crypto"
    / "btc"
    / "rsi_atr_stop_strategy.yaml"
)


class RsiAtrStrategyConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    input_panel: Path
    output_panel: Path
    rsi_window: int
    atr_window: int
    oversold_threshold: float
    stop_multiple: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the BTC RSI/ATR strategy feature panel."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to the strategy YAML config. Defaults to {DEFAULT_CONFIG_PATH}.",
    )
    return parser.parse_args()


def resolve_repo_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path

    return REPO_ROOT / path


def load_strategy_config(config_path: Path) -> RsiAtrStrategyConfig:
    config_path = config_path if config_path.is_absolute() else REPO_ROOT / config_path
    with config_path.open(encoding="utf-8") as config_file:
        raw_config: dict[str, Any] = yaml.safe_load(config_file)

    paths = raw_config["paths"]
    parameters = raw_config["parameters"]

    return RsiAtrStrategyConfig(
        input_panel=resolve_repo_path(str(paths["input_panel"])),
        output_panel=resolve_repo_path(str(paths["output_panel"])),
        rsi_window=int(parameters["rsi_window"]),
        atr_window=int(parameters["atr_window"]),
        oversold_threshold=float(parameters["oversold_threshold"]),
        stop_multiple=float(parameters["stop_multiple"]),
    )


def calculate_wilder_rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    average_loss = losses.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()

    relative_strength = average_gain / average_loss
    rsi = 100 - (100 / (1 + relative_strength))
    return rsi


def calculate_wilder_atr(frame: pd.DataFrame, window: int) -> pd.Series:
    previous_close = frame["close"].shift(1)
    true_range = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous_close).abs(),
            (frame["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return true_range.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()


def build_entry_state(
    rsi: pd.Series,
    *,
    oversold_threshold: float,
) -> tuple[pd.Series, pd.Series]:
    armed_values: list[bool] = []
    buy_signal_values: list[bool] = []
    armed = False

    for value in rsi:
        buy_signal = False
        if pd.notna(value):
            # TODO: maybe adjust this i.e. add some percentage margin to the threshold 
            # this to prevent buying when the price is just retesting the RSI 30 threshold and then falls again
            if armed and value > oversold_threshold:
                buy_signal = True
                armed = False
            elif value < oversold_threshold:
                armed = True

        armed_values.append(armed)
        buy_signal_values.append(buy_signal)

    return (
        pd.Series(armed_values, index=rsi.index, dtype="bool"),
        pd.Series(buy_signal_values, index=rsi.index, dtype="bool"),
    )


def validate_input_panel(panel: pd.DataFrame) -> None:
    required_columns = {"date", "timestamp", "symbol", "open", "high", "low", "close"}
    missing_columns = sorted(required_columns - set(panel.columns))
    if missing_columns:
        raise ValueError(
            f"Input panel is missing required columns: {', '.join(missing_columns)}"
        )

    symbols = sorted(panel["symbol"].astype(str).str.upper().unique().tolist())
    if symbols != ["BTCUSDT"]:
        raise ValueError(
            "RSI/ATR BTC strategy expects a BTCUSDT cleaned panel; "
            f"found symbols: {', '.join(symbols)}"
        )


def build_feature_panel(
    panel: pd.DataFrame,
    config: RsiAtrStrategyConfig,
) -> pd.DataFrame:
    validate_input_panel(panel)
    feature_panel = panel.copy()
    feature_panel["date"] = pd.to_datetime(feature_panel["date"], errors="raise")
    feature_panel = feature_panel.sort_values(["date", "symbol"]).reset_index(drop=True)

    for column in ("open", "high", "low", "close"):
        feature_panel[column] = pd.to_numeric(feature_panel[column], errors="raise")

    rsi_column = f"rsi_{config.rsi_window}"
    atr_column = f"atr_{config.atr_window}"
    feature_panel[rsi_column] = calculate_wilder_rsi(
        feature_panel["close"],
        config.rsi_window,
    )
    feature_panel[atr_column] = calculate_wilder_atr(feature_panel, config.atr_window)

    armed, buy_signal = build_entry_state(
        feature_panel[rsi_column],
        oversold_threshold=config.oversold_threshold,
    )
    feature_panel["oversold_armed"] = armed
    feature_panel["buy_signal"] = buy_signal
    feature_panel["initial_stop_price"] = pd.NA
    feature_panel.loc[feature_panel["buy_signal"], "initial_stop_price"] = (
        feature_panel.loc[feature_panel["buy_signal"], "close"]
        - config.stop_multiple * feature_panel.loc[feature_panel["buy_signal"], atr_column]
    )

    feature_panel["date"] = feature_panel["date"].dt.strftime("%Y-%m-%d")
    return feature_panel


def write_feature_panel(feature_panel: pd.DataFrame, output_panel: Path) -> None:
    output_panel.parent.mkdir(parents=True, exist_ok=True)
    feature_panel.to_csv(output_panel, index=False)


def main() -> None:
    args = parse_args()
    config = load_strategy_config(args.config)
    panel = pd.read_csv(config.input_panel)
    feature_panel = build_feature_panel(panel, config)
    write_feature_panel(feature_panel, config.output_panel)
    print(f"Wrote {len(feature_panel)} rows to {config.output_panel}")


if __name__ == "__main__":
    main()
