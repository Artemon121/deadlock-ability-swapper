import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = (Path(__file__).parent / "config.toml").resolve()


@dataclass
class Config:
    deadlock_path: Path
    heroes_vdata_path: Path
    output_path: Path
    theme: str

    @staticmethod
    def load(path: Path = CONFIG_PATH) -> "Config":
        """Load configuration from TOML file"""
        if not path.exists():
            raise FileNotFoundError(f"Config not found at {path}")

        with open(path, "rb") as f:
            data = tomllib.load(f)

        return Config(
            deadlock_path=Path(data["deadlock_path"]).resolve(),
            heroes_vdata_path=Path(data["heroes_vdata_path"]).resolve(),
            output_path=Path(data["output_path"]).resolve(),
            theme=data["theme"],
        )
