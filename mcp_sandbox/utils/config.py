import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler("docker_manager.log")]
)
logger = logging.getLogger("DockerManager")

# Create results directory (make absolute)
RESULTS_DIR = Path("results").resolve()
RESULTS_DIR.mkdir(exist_ok=True)

# Base URL for file access
BASE_URL = "http://localhost:8000/static/"  # TODO: Make configurable

# Default Docker image name
DEFAULT_DOCKER_IMAGE = "python-sandbox:latest" 