from pathlib import Path
import pathlib
import typing as t

from pydantic import BaseModel
from strictyaml import load, YAML

# Project Directories
PACKAGE_ROOT = Path.cwd() / "BitcoinOptionTrading"
CONFIG_FILE_PATH = PACKAGE_ROOT  / "config.yaml"
DATA_DIR = PACKAGE_ROOT / "data"
PLOT_DIR = PACKAGE_ROOT / "plots"


class AppConfig(BaseModel):
    """
    Application-level config.
    """

    package_name: str
    BTCUSD_deribit: str
    BTCUSD_binance: str
    all_trades_deribit: str
    option_table: str
    bandwidths_table: pathlib.Path

    data_raw: pathlib.Path
    data_rnd: pathlib.Path
    data_garch: pathlib.Path
    data_densities: pathlib.Path
    data_trades: pathlib.Path
    plot_dir: pathlib.Path


class ModelConfig(BaseModel):
    """
    All configuration relevant to model
    training and feature engineering.
    """

    random_state: int
    tau_section: str
    cutoff: float

    kernel: str
    gridsize: int
    sampling: str
    n_sections: int
    loss: str

    simulations: int
    n_fits: int
    window_length: int
    variate_GARCH_parameters: bool

    similarity_threshold: float
    cut_tail_percent: float

    target: str
    rnd_input_features: t.Sequence[str]
    hd_input_features: t.Sequence[str]


class Config(BaseModel):
    """Master config object."""

    app_config: AppConfig
    model_config: ModelConfig


def find_config_file() -> Path:
    """Locate the configuration file."""
    if CONFIG_FILE_PATH.is_file():
        return CONFIG_FILE_PATH
    raise Exception(f"Config not found at {CONFIG_FILE_PATH!r}")


def fetch_config_from_yaml(cfg_path: Path = None) -> YAML:
    """Parse YAML containing the package configuration."""

    if not cfg_path:
        cfg_path = find_config_file()

    if cfg_path:
        with open(cfg_path, "r") as conf_file:
            parsed_config = load(conf_file.read())
            return parsed_config
    raise OSError(f"Did not find config file at path: {cfg_path}")


def create_and_validate_config(parsed_config: YAML = None) -> Config:
    """Run validation on config values."""
    if parsed_config is None:
        parsed_config = fetch_config_from_yaml()

    # specify the data attribute from the strictyaml YAML type.
    _config = Config(
        app_config=AppConfig(**parsed_config.data),
        model_config=ModelConfig(**parsed_config.data),
    )

    # add DATASET_DIR prefix
    _config.app_config.data_raw = DATA_DIR / _config.app_config.data_raw
    _config.app_config.data_rnd = DATA_DIR / _config.app_config.data_rnd
    _config.app_config.data_garch = DATA_DIR / _config.app_config.data_garch
    _config.app_config.data_densities = DATA_DIR / _config.app_config.data_densities
    _config.app_config.data_trades = DATA_DIR / _config.app_config.data_trades
    _config.app_config.bandwidths_table = _config.app_config.data_rnd / _config.app_config.bandwidths_table
    _config.app_config.plot_dir = PLOT_DIR

    return _config


config = create_and_validate_config()
