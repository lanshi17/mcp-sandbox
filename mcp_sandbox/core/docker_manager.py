import uuid
import re
import docker
import threading
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional, Any
from contextlib import contextmanager
from pathlib import Path

from mcp_sandbox.utils.config import logger, DEFAULT_DOCKER_IMAGE, config

class DockerManager:
    """Manage Docker sandboxes with automatic creation"""
    
    def __init__(self, base_image: str = DEFAULT_DOCKER_IMAGE):
        self.base_image = base_image
        self.sandbox_last_used: Dict[str, datetime] = {}
        self.session_sandbox_map: Dict[str, str] = {}
        self.package_install_status: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}", exc_info=True)
            raise
        
        # Try to build our own image if needed
        self._ensure_docker_image()
        
        # Load existing sandboxes
        self._load_sandbox_records()
        
        logger.info(f"DockerManager initialized, using base image: {self.base_image}")
    
    def _ensure_docker_image(self):
        """Ensure our custom Docker image exists, build it if needed"""
        custom_image_name = DEFAULT_DOCKER_IMAGE
        dockerfile_path = Path(config["docker"].get("dockerfile_path", "Dockerfile")).resolve()
        build_info_file = Path(config["docker"].get("build_info_file", ".docker_build_info")).resolve()
        check_changes = config["docker"].get("check_dockerfile_changes", True)
        
        # Check if image already exists
        image_exists = True
        try:
            self.docker_client.images.get(custom_image_name)
            logger.info(f"Docker image exists: {custom_image_name}")
        except docker.errors.ImageNotFound:
            image_exists = False
            logger.info(f"Docker image not found: {custom_image_name}")
        
        # Determine if we need to (re)build the image
        need_rebuild = not image_exists
        
        # Check for Dockerfile changes if enabled
        if image_exists and check_changes and dockerfile_path.exists():
            # Calculate current Dockerfile hash
            current_hash = self._get_file_hash(dockerfile_path)
            
            # Get previous build info if available
            previous_hash = None
            if build_info_file.exists():
                try:
                    with open(build_info_file, 'r') as f:
                        build_info = json.load(f)
                        previous_hash = build_info.get('dockerfile_hash')
                        logger.info(f"Found previous build info with hash: {previous_hash}")
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Could not read build info file: {e}")
            
            # If hash is different or no previous hash, we need to rebuild
            if previous_hash != current_hash:
                logger.info(f"Dockerfile has changed (Previous: {previous_hash}, Current: {current_hash})")
                need_rebuild = True
        
        # Build the image if needed
        if need_rebuild:
            if not dockerfile_path.exists():
                logger.error("Dockerfile not found, falling back to base image")
                return
            
            try:
                logger.info(f"Building Docker image: {custom_image_name}")
                
                # Build the image
                _, logs = self.docker_client.images.build(
                    path=str(dockerfile_path.parent), 
                    dockerfile=str(dockerfile_path.name),
                    tag=custom_image_name,
                    rm=True,
                    forcerm=True
                )
                
                # Log build output
                for log in logs:
                    if 'stream' in log:
                        logger.info(log['stream'].strip())
                
                # Save build info
                if check_changes:
                    build_info = {
                        'dockerfile_hash': self._get_file_hash(dockerfile_path),
                        'build_time': datetime.now().isoformat(),
                        'image_name': custom_image_name
                    }
                    with open(build_info_file, 'w') as f:
                        json.dump(build_info, f)
                        logger.info(f"Saved build info to {build_info_file}")
                
                self.base_image = custom_image_name
                logger.info(f"Successfully built Docker image: {custom_image_name}")
            except Exception as e:
                logger.error(f"Failed to build Docker image: {e}", exc_info=True)
    
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
            sandboxes = self.docker_client.containers.list(all=True, filters={"label": "python-sandbox"})
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
            # Check if sandbox still exists
            try:
                self.docker_client.containers.get(sandbox_id)
                self.sandbox_last_used[sandbox_id] = datetime.now()
                logger.info(f"Session {session_id} using existing sandbox {sandbox_id}")
                return sandbox_id
            except docker.errors.NotFound:
                logger.info(f"Sandbox {sandbox_id} for session {session_id} not found, creating new one")
                pass
        
        # Create new sandbox
        sandbox_id = self.create_sandbox()
        self.session_sandbox_map[session_id] = sandbox_id
        logger.info(f"Created new sandbox {sandbox_id} for session {session_id}")
        return sandbox_id
    
    def create_sandbox(self) -> str:
        """Create a new Docker sandbox and return its ID"""
        sandbox_name = f"python-sandbox-{str(uuid.uuid4())[:8]}"
        
        try:
            # Create sandbox with proper security constraints
            sandbox = self.docker_client.containers.create(
                image=self.base_image,
                name=sandbox_name,
                detach=True,
                working_dir='/app/results',
                labels={"python-sandbox": "true"},
                # Security constraints
                mem_limit='1g',  # Limit memory
                memswap_limit='1g',  # Disable swap
                network_mode='bridge',  # Allow network access
                privileged=False,
                cap_drop=['ALL'],
                security_opt=['no-new-privileges'],
            )
            
            # Start sandbox
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
            self.docker_client.containers.get(sandbox_id)
            self.sandbox_last_used[sandbox_id] = datetime.now()
            return None
        except docker.errors.NotFound as e:
            return {"error": True, "message": str(e) or f"Sandbox not found: {sandbox_id}"}
    
    
    @contextmanager
    def _get_running_sandbox(self, sandbox_id: str):
        """Context manager to get a running sandbox, with auto-restart if needed"""
        try:
            sandbox = self.docker_client.containers.get(sandbox_id)
            
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
    
    def list_files_in_sandbox(self, sandbox_id: str, directory: str = "/app/results", with_stat: bool = False) -> list:
        """List files in a directory inside the sandbox. If with_stat=True, return (filename, ctime) tuples."""
        try:
            sandbox = self.docker_client.containers.get(sandbox_id)
            exec_result = sandbox.exec_run(f"ls -1 {directory}")
            if exec_result.exit_code != 0:
                return []
            files = exec_result.output.decode().splitlines()
            full_paths = [f"{directory.rstrip('/')}/{f}" for f in files]
            if with_stat:
                # Get ctime for each file
                stat_files = []
                for f in full_paths:
                    stat_result = sandbox.exec_run(f'stat -c "%n|%Z" "{f}"')
                    if stat_result.exit_code == 0:
                        parts = stat_result.output.decode().strip().split("|", 1)
                        if len(parts) == 2:
                            stat_files.append((parts[0], int(parts[1])))
                return stat_files
            else:
                return full_paths
        except Exception as e:
            logger.error(f"Failed to list files in sandbox {sandbox_id}: {e}")
            return []

    def get_file_link(self, sandbox_id: str, file_path: str) -> str:
        """Return the full API link to download a file from a sandbox, using config.BASE_URL if available."""
        base_url = getattr(config, "BASE_URL", None) or "http://localhost:8000"
        return f"{base_url}/sandbox/file?sandbox_id={sandbox_id}&file_path={file_path}"
    
    def execute_python_code(self, sandbox_id: str, code: str) -> Dict[str, Any]:
        """Execute Python code in a Docker sandbox and return files created/modified after start time."""
        error = self.verify_sandbox_exists(sandbox_id)
        if error:
            return error

        # Get current timestamp, only return files with ctime >= start_ts
        import time
        start_ts = int(time.time())

        logger.info("Executing code:")
        logger.info("=" * 50)
        logger.info(code)
        logger.info("=" * 50)
        logger.info(f"Running code in sandbox {sandbox_id}")

        try:
            with self._get_running_sandbox(sandbox_id) as sandbox:
                # Write Python code to a temporary file, then execute that file in the sandbox
                # This avoids issues with quotes and special characters in command line
                temp_code_file = "/tmp/code_to_run.py"
                
                # 1. Write the code to a temporary file inside the sandbox
                write_code_cmd = f"cat > {temp_code_file} << 'EOL'\n{code}\nEOL"
                write_result = sandbox.exec_run(
                    cmd=["sh", "-c", write_code_cmd],
                    workdir="/app/results",
                    privileged=False
                )
                
                if write_result.exit_code != 0:
                    logger.error(f"Failed to write code to sandbox: {write_result.output.decode('utf-8')}")
                    return {
                        "error": "Failed to prepare code execution",
                        "stdout": "",
                        "stderr": write_result.output.decode('utf-8'),
                        "exit_code": write_result.exit_code,
                        "files": [],
                        "file_links": []
                    }
                
                # 2. Execute the code from the temporary file
                exec_result = sandbox.exec_run(
                    cmd=["python", temp_code_file],
                    workdir="/app/results",
                    stdout=True,
                    stderr=True,
                    demux=True,  # Separate stdout and stderr
                    privileged=False
                )
                
                exit_code = exec_result.exit_code
                stdout_bytes, stderr_bytes = exec_result.output
                
                stdout = stdout_bytes.decode('utf-8') if stdout_bytes else ""
                stderr = stderr_bytes.decode('utf-8') if stderr_bytes else ""
                
                # 3. Remove the temporary file
                sandbox.exec_run(
                    cmd=["rm", "-f", temp_code_file],
                    privileged=False
                )
                
                # Get all files and their ctime after execution
                all_files = self.list_files_in_sandbox(sandbox_id, with_stat=True)
                new_files = [f for f, ctime in all_files if ctime >= start_ts]
                file_links = [self.get_file_link(sandbox_id, f) for f in new_files]
                
                # Log execution results
                logger.info("Execution results:")
                logger.info(f"Exit code: {exit_code}")
                if stdout:
                    logger.info("Stdout:")
                    logger.info(stdout)
                if stderr:
                    logger.warning("Stderr:")
                    logger.warning(stderr)
                
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "files": new_files,
                    "file_links": file_links
                }
        except ValueError as e:
            # Sandbox not found error from context manager
            return {
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "files": [],
                "file_links": []
            }
        except Exception as e:
            logger.error(f"Failed to run code in sandbox {sandbox_id}: {e}", exc_info=True)
            
            # Try to capture detailed error information
            error_message = str(e)
            if hasattr(e, 'stderr') and e.stderr:
                stderr = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
                error_message = f"{error_message}\nDetails: {stderr}"
            
            return {
                "error": error_message,
                "stdout": "",
                "stderr": error_message,
                "exit_code": 1,
                "files": [],
                "file_links": []
            }
    
    def _get_pip_index_url(self):
        # Try to get PyPI index URL from config, fallback to empty string
        try:
            return config.get("pypi_index_url", "")
        except Exception:
            return ""

    def _install_package_sync(self, sandbox_id: str, package_name: str) -> Dict[str, Any]:
        """Synchronously install package and return result"""
        status_key = f"{sandbox_id}:{package_name}"
        
        try:
            with self._get_running_sandbox(sandbox_id) as sandbox:
                # Activate venv and install package
                pip_index_url = self._get_pip_index_url()
                pip_index_opt = f" --index-url {pip_index_url}" if pip_index_url else ""
                exec_result = sandbox.exec_run(
                    cmd=f"uv pip install{pip_index_opt} {package_name}",
                    stdout=True,
                    stderr=True,
                    privileged=False
                )
                
                exit_code = exec_result.exit_code
                output = exec_result.output.decode('utf-8')
                
                # Log the output
                logger.info(f"Package installation output: {output}")
                logger.info(f"Exit code: {exit_code}")
                
                # Update installation status
                if exit_code == 0:
                    status = {
                        "status": "success",
                        "message": f"Successfully installed {package_name}",
                        "complete": True,
                        "success": True,
                        "end_time": datetime.now()
                    }
                    self.package_install_status[status_key] = status
                    return status
                else:
                    status = {
                        "status": "failed",
                        "message": f"Failed to install {package_name}: {output}",
                        "stderr": output,
                        "complete": True,
                        "success": False,
                        "end_time": datetime.now()
                    }
                    self.package_install_status[status_key] = status
                    return status
        except Exception as e:
            logger.error(f"Failed to install package {package_name} for sandbox {sandbox_id}: {e}", exc_info=True)
            
            # Get more detailed error information
            error_message = str(e)
            if hasattr(e, 'stderr') and e.stderr:
                stderr = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
                error_message = f"{error_message}\nDetails: {stderr}"
            
            status = {
                "status": "failed",
                "message": f"Error: {error_message}",
                "stderr": error_message,
                "complete": True,
                "success": False,
                "end_time": datetime.now()
            }
            self.package_install_status[status_key] = status
            return status
    
    def install_package(self, sandbox_id: str, package_name: str) -> Dict[str, Any]:
        """Install package, directly return success if completes within 5 seconds"""
        # Verify sandbox exists
        error = self.verify_sandbox_exists(sandbox_id)
        if error:
            return error
        
        logger.info(f"Starting installation of package {package_name} for sandbox {sandbox_id}")
        status_key = f"{sandbox_id}:{package_name}"
        
        # Check if already installing
        if status_key in self.package_install_status:
            status = self.package_install_status[status_key]
            if status["status"] == "installing" and not status["complete"]:
                return {
                    "success": None,
                    "status": "installing",
                    "message": f"Package {package_name} installation already in progress"
                }
        
        # Mark as installing for tracking
        self.package_install_status[status_key] = {
            "status": "installing",
            "start_time": datetime.now(),
            "message": f"Installing {package_name}...",
            "complete": False
        }
        
        # Create and start installation in a separate thread that we'll monitor
        install_thread = threading.Thread(
            target=self._install_package_sync,
            args=(sandbox_id, package_name),
            daemon=True
        )
        install_thread.start()
        
        # Wait up to 5 seconds for installation to complete
        try:
            import time
            start_time = time.time()
            max_wait = 5  # seconds
            
            while time.time() - start_time < max_wait:
                # Check if installation completed
                if status_key in self.package_install_status:
                    status = self.package_install_status[status_key]
                    if status.get("complete", False):
                        # Installation completed within 5 seconds
                        logger.info(f"Package {package_name} installed within 5 seconds: {status}")
                        return status
                
                # Sleep a short time before checking again
                time.sleep(0.1)
            
            # If we're here, installation is taking longer than 5 seconds
            logger.info(f"Installation of {package_name} is taking longer than 5 seconds, continuing in background")
            
            # Note: We don't start a new thread, the original one continues in background
            return {
                "success": None,
                "status": "installing",
                "message": f"Installation of {package_name} in progress. Use check_package_status to monitor progress."
            }
            
        except Exception as e:
            logger.error(f"Error while monitoring installation: {e}", exc_info=True)
            # Let the installation continue in background
            return {
                "success": None,
                "status": "installing",
                "message": f"Installation of {package_name} in progress. Use check_package_status to monitor progress."
            }
    
    def check_package_status(self, sandbox_id: str, package_name: str) -> Dict[str, Any]:
        """Check the installation status of a package"""
        # Verify sandbox exists
        error = self.verify_sandbox_exists(sandbox_id)
        if error:
            return error
        
        status_key = f"{sandbox_id}:{package_name}"
        
        # If we have a record and it's complete, return it immediately
        if status_key in self.package_install_status:
            status = self.package_install_status[status_key]
            if status.get("complete", False):
                return status
        
        # If installation is in progress, wait up to 5 seconds for completion
        if status_key in self.package_install_status and self.package_install_status[status_key]["status"] == "installing":
            try:
                import time
                start_time = time.time()
                max_wait = 5  # seconds
                
                while time.time() - start_time < max_wait:
                    # Refresh status
                    status = self.package_install_status[status_key]
                    
                    # If installation completed, return status immediately
                    if status.get("complete", False):
                        logger.info(f"Package {package_name} installation completed within check window")
                        return status
                    
                    # Sleep a short time before checking again
                    time.sleep(0.1)
                
                # If we're here, installation is still in progress after 5 seconds
                logger.info(f"Package {package_name} installation still in progress after 5 seconds")
                
                # Calculate elapsed time
                elapsed_time = datetime.now() - status["start_time"]
                status["elapsed_seconds"] = elapsed_time.total_seconds()
                
                return status
            except Exception as e:
                logger.error(f"Error while waiting for package status: {e}", exc_info=True)
                # Continue with regular status check
        
        # If no installation record found
        if status_key not in self.package_install_status:
            # Check if package is already installed (might have been installed without tracking)
            try:
                with self._get_running_sandbox(sandbox_id) as sandbox:
                    # Use pip list and filter results to check if package is installed
                    exec_result = sandbox.exec_run(
                        cmd=f"uv pip list | grep -i {package_name}",
                        stdout=True,
                        stderr=True,
                        privileged=False
                    )
                    
                    output = exec_result.output.decode('utf-8').strip()
                    
                    if output and package_name.lower() in output.lower():
                        return {
                            "status": "success",
                            "message": f"Package {package_name} is already installed",
                            "complete": True,
                            "success": True
                        }
                    else:
                        return {
                            "status": "not_found",
                            "message": f"No installation record found for {package_name}",
                            "complete": True,
                            "success": False
                        }
            except Exception as e:
                logger.error(f"Error checking if package {package_name} is installed: {e}")
                return {
                    "status": "error",
                    "message": f"Error checking package status: {str(e)}",
                    "complete": True,
                    "success": False
                }
        
        # Return recorded status
        status = self.package_install_status[status_key]
        
        # If installation is in progress, calculate elapsed time
        if status["status"] == "installing" and not status.get("complete", False):
            elapsed_time = datetime.now() - status["start_time"]
            status["elapsed_seconds"] = elapsed_time.total_seconds()
        
        return status
    
    def list_sandboxes(self) -> list:
        """List all Docker sandboxes managed by this service (with label python-sandbox)."""
        sandboxes = []
        for sandbox in self.docker_client.containers.list(all=True, filters={"label": "python-sandbox"}):
            sandbox_info = {
                "sandbox_id": sandbox.id,
                "name": sandbox.name,
                "status": sandbox.status,
                "image": sandbox.image.tags[0] if sandbox.image.tags else sandbox.image.short_id,
                "created": sandbox.attrs["Created"],
                "last_used": self.sandbox_last_used.get(sandbox.id),
            }
            sandboxes.append(sandbox_info)
        return sandboxes
    
    def list_installed_packages(self, sandbox_id: str) -> list:
        """Return a list of installed Python packages in the given sandbox, robustly parsing uv output."""
        try:
            sandbox = self.docker_client.containers.get(sandbox_id)
            exec_result = sandbox.exec_run('uv pip list --format=json')
            output = exec_result.output.decode()
            # Extract the first JSON array from the output
            match = re.search(r'\[.*\]', output, re.DOTALL)
            if match:
                json_str = match.group(0)
                try:
                    return json.loads(json_str)
                except Exception as parse_err:
                    logger.error(f"[list_installed_packages] JSON parse error: {parse_err} | json_str={json_str!r}")
                    return []
            else:
                logger.warning(f"[list_installed_packages] No JSON array found in output: {output!r}")
                return []
        except Exception as e:
            logger.error(f"[list_installed_packages] Error listing packages in {sandbox_id}: {e}", exc_info=True)
            return []