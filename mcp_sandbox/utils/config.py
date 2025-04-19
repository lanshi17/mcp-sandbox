import logging
import os
import tomli
from pathlib import Path

# Load configuration from TOML file
CONFIG_FILE = Path("config.toml").resolve()

# Default configuration if file doesn't exist
DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
    },
    "paths": {
        "results_dir": "results",
    },
    "docker": {
        "default_image": "python-sandbox:latest",
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_file": "mcp_sandbox.log",
    },
}

# Load configuration
try:
    with open(CONFIG_FILE, "rb") as f:
        config = tomli.load(f)
    logging.info(f"Loaded configuration from {CONFIG_FILE}")
except (FileNotFoundError, tomli.TOMLDecodeError) as e:
    logging.warning(f"Could not load configuration file: {e}. Using default configuration.")
    config = DEFAULT_CONFIG

# Extract configuration values
HOST = os.environ.get("APP_HOST", config["server"]["host"])
PORT = int(os.environ.get("APP_PORT", config["server"]["port"]))
RESULTS_DIR = Path(config["paths"]["results_dir"]).resolve()
DEFAULT_DOCKER_IMAGE = config["docker"]["default_image"]

# Base URL for file access
BASE_URL = f"http://{'localhost' if HOST == '0.0.0.0' else HOST}:{PORT}/static/"

# Create results directory (make absolute)
RESULTS_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config["logging"]["level"]),
    format=config["logging"]["format"],
    handlers=[logging.StreamHandler(), logging.FileHandler(config["logging"]["log_file"])]
)
logger = logging.getLogger("MCP_SANDBOX") 