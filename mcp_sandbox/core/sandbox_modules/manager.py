import uuid
import json
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path
import hashlib
from contextlib import contextmanager
from mcp_sandbox.utils.config import logger, DEFAULT_DOCKER_IMAGE, config
import docker

class SandboxManager:
    """Manage Sandboxes with automatic creation"""
    def __init__(self, base_image: str = DEFAULT_DOCKER_IMAGE):
        self.base_image = base_image
        self.sandbox_last_used: Dict[str, datetime] = {}
        self.session_sandbox_map: Dict[str, str] = {}
        self.package_install_status: Dict[str, Dict[str, Any]] = {}
        try:
            self.sandbox_client = docker.from_env()
            logger.info("Sandbox client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Sandbox client: {e}", exc_info=True)
            raise
        self._ensure_sandbox_image()
        self._load_sandbox_records()
        logger.info(f"SandboxManager initialized, using base image: {self.base_image}")

    def _ensure_sandbox_image(self):
        """Ensure our custom Sandbox image exists, build it if needed"""
        custom_image_name = DEFAULT_DOCKER_IMAGE
        sandboxfile_path = Path(config["docker"].get("dockerfile_path", "Dockerfile")).resolve()
        build_info_file = Path(config["docker"].get("build_info_file", ".docker_build_info")).resolve()
        check_changes = config["docker"].get("check_dockerfile_changes", True)
        image_exists = True
        try:
            self.sandbox_client.images.get(custom_image_name)
            logger.info(f"Sandbox image exists: {custom_image_name}")
        except docker.errors.ImageNotFound:
            image_exists = False
            logger.info(f"Sandbox image not found: {custom_image_name}")
        need_rebuild = not image_exists
        if image_exists and check_changes and sandboxfile_path.exists():
            current_hash = self._get_file_hash(sandboxfile_path)
            previous_hash = None
            if build_info_file.exists():
                try:
                    with open(build_info_file, 'r') as f:
                        build_info = json.load(f)
                        previous_hash = build_info.get('dockerfile_hash')
                        logger.info(f"Found previous build info with hash: {previous_hash}")
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Could not read build info file: {e}")
            if previous_hash != current_hash:
                logger.info(f"Sandboxfile has changed (Previous: {previous_hash}, Current: {current_hash})")
                need_rebuild = True
        if need_rebuild:
            if not sandboxfile_path.exists():
                logger.error("Sandboxfile not found, falling back to base image")
                return
            try:
                logger.info(f"Building Sandbox image: {custom_image_name}")
                _, logs = self.sandbox_client.images.build(
                    path=str(sandboxfile_path.parent),
                    dockerfile=str(sandboxfile_path.name),
                    tag=custom_image_name,
                    rm=True,
                    forcerm=True
                )
                for log in logs:
                    if 'stream' in log:
                        logger.info(log['stream'].strip())
                if check_changes:
                    build_info = {
                        'dockerfile_hash': self._get_file_hash(sandboxfile_path),
                        'build_time': datetime.now().isoformat(),
                        'image_name': custom_image_name
                    }
                    with open(build_info_file, 'w') as f:
                        json.dump(build_info, f)
                        logger.info(f"Saved build info to {build_info_file}")
                self.base_image = custom_image_name
                logger.info(f"Successfully built Sandbox image: {custom_image_name}")
            except Exception as e:
                logger.error(f"Failed to build Sandbox image: {e}", exc_info=True)

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file to detect changes"""
        if not file_path.exists():
            return ""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except IOError as e:
            logger.error(f"Error reading file for hashing: {e}")
            return ""

    def _load_sandbox_records(self) -> None:
        """Load existing sandbox usage records"""
        try:
            sandboxes = self.sandbox_client.containers.list(all=True, filters={"label": "python-sandbox"})
            for sandbox in sandboxes:
                sandbox_id = sandbox.id
                self.sandbox_last_used[sandbox_id] = datetime.now()
                logger.info(f"Loaded existing sandbox: {sandbox_id}")
        except Exception as e:
            logger.error(f"Failed to load existing sandboxes: {e}", exc_info=True)

    def get_sandbox_for_session(self, session_id: str) -> str:
        """Get sandbox ID for a session, create new one if not exists"""
        if session_id in self.session_sandbox_map:
            sandbox_id = self.session_sandbox_map[session_id]
            try:
                self.sandbox_client.containers.get(sandbox_id)
                self.sandbox_last_used[sandbox_id] = datetime.now()
                logger.info(f"Session {session_id} using existing sandbox {sandbox_id}")
                return sandbox_id
            except docker.errors.NotFound:
                logger.info(f"Sandbox {sandbox_id} for session {session_id} not found, creating new one")
        sandbox_id = self.create_sandbox()
        self.session_sandbox_map[session_id] = sandbox_id
        logger.info(f"Created new sandbox {sandbox_id} for session {session_id}")
        return sandbox_id

    def create_sandbox(self) -> str:
        """Create a new Sandbox and return its ID"""
        sandbox_name = f"python-sandbox-{str(uuid.uuid4())[:8]}"
        try:
            sandbox = self.sandbox_client.containers.create(
                image=self.base_image,
                name=sandbox_name,
                detach=True,
                working_dir='/app/results',
                labels={"python-sandbox": "true"},
                mem_limit='1g',
                memswap_limit='1g',
                network_mode='bridge',
                privileged=False,
                cap_drop=['ALL'],
                security_opt=['no-new-privileges'],
            )
            sandbox.start()
            sandbox_id = sandbox.id
            self.sandbox_last_used[sandbox_id] = datetime.now()
            logger.info(f"Created new sandbox: {sandbox_id} (name: {sandbox_name})")
            return sandbox_id
        except Exception as e:
            logger.error(f"Failed to create sandbox: {e}", exc_info=True)
            raise

    def verify_sandbox_exists(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Verify sandbox exists and clean up if not. Returns error dict if not exists."""
        if sandbox_id not in self.sandbox_last_used:
            return {"error": True, "message": f"Sandbox not found: {sandbox_id}"}
        try:
            self.sandbox_client.containers.get(sandbox_id)
            self.sandbox_last_used[sandbox_id] = datetime.now()
            return None
        except docker.errors.NotFound as e:
            return {"error": True, "message": str(e) or f"Sandbox not found: {sandbox_id}"}

    @contextmanager
    def _get_running_sandbox(self, sandbox_id: str):
        """Context manager to get a running sandbox, with auto-restart if needed"""
        try:
            sandbox = self.sandbox_client.containers.get(sandbox_id)
            
            # Ensure sandbox is running
            if sandbox.status != "running":
                logger.info(f"Sandbox {sandbox_id} is not running. Current status: {sandbox.status}")
                
                # If sandbox status is exited, try to get sandbox logs to understand why
                if sandbox.status == "exited":
                    try:
                        logs = sandbox.logs().decode('utf-8', errors='replace')
                        logger.warning(f"Sandbox {sandbox_id} exited. Sandbox logs: {logs}")
                    except Exception as log_err:
                        logger.error(f"Failed to get logs for exited sandbox {sandbox_id}: {log_err}")
                
                # Try to start the sandbox
                logger.info(f"Attempting to start sandbox {sandbox_id}...")
                sandbox.start()
                sandbox.reload()
                logger.info(f"Sandbox {sandbox_id} started successfully.")
            
            yield sandbox
            
        except docker.errors.NotFound:
            logger.error(f"Sandbox {sandbox_id} not found during operation.")
            raise ValueError(f"Sandbox {sandbox_id} not found.")
