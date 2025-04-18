import uuid
import docker
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple
from contextlib import contextmanager
from pathlib import Path

from mcp_sandbox.utils.config import logger, RESULTS_DIR, DEFAULT_DOCKER_IMAGE
from mcp_sandbox.utils.file_manager import collect_output_files, check_and_delete_files, cleanup_container_files

class DockerManager:
    """Manage Docker containers with automatic creation and cleanup"""
    
    def __init__(self, base_image: str = DEFAULT_DOCKER_IMAGE, cleanup_after_hours: int = 1):
        self.base_image = base_image
        self.cleanup_after_hours = cleanup_after_hours
        self.container_last_used: Dict[str, datetime] = {}
        self.session_container_map: Dict[str, str] = {}
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
        
        # Load existing containers
        self._load_container_records()
        
        logger.info(f"DockerManager initialized, using base image: {self.base_image}")
    
    def _ensure_docker_image(self):
        """Ensure our custom Docker image exists, build it if needed"""
        custom_image_name = "python-sandbox:latest"
        
        try:
            # Check if image exists
            self.docker_client.images.get(custom_image_name)
            logger.info(f"Using existing Docker image: {custom_image_name}")
        except docker.errors.ImageNotFound:
            # Build the image
            logger.info(f"Building Docker image: {custom_image_name}")
            try:
                dockerfile_path = Path("Dockerfile").resolve()
                if not dockerfile_path.exists():
                    logger.error("Dockerfile not found, falling back to base image")
                    return
                
                # Build the image
                _, logs = self.docker_client.images.build(
                    path=".", 
                    tag=custom_image_name,
                    rm=True
                )
                for log in logs:
                    if 'stream' in log:
                        logger.info(log['stream'].strip())
                        
                self.base_image = custom_image_name
                logger.info(f"Successfully built Docker image: {custom_image_name}")
            except Exception as e:
                logger.error(f"Failed to build Docker image: {e}", exc_info=True)
    
    def _load_container_records(self) -> None:
        """Load existing container usage records"""
        try:
            containers = self.docker_client.containers.list(all=True, filters={"label": "python-sandbox"})
            for container in containers:
                container_id = container.id
                # Set last used time of existing containers to 23 hours ago
                # So they will be deleted in the next cleanup if not used
                self.container_last_used[container_id] = datetime.now() - timedelta(hours=23)
                logger.info(f"Loaded existing container: {container_id}")
        except Exception as e:
            logger.error(f"Failed to load existing containers: {e}", exc_info=True)
    
    def get_container_for_session(self, session_id: str) -> str:
        """Get container ID for a session, create new one if not exists"""
        if session_id in self.session_container_map:
            container_id = self.session_container_map[session_id]
            # Check if container still exists
            try:
                self.docker_client.containers.get(container_id)
                self.container_last_used[container_id] = datetime.now()
                logger.info(f"Session {session_id} using existing container {container_id}")
                return container_id
            except docker.errors.NotFound:
                logger.info(f"Container {container_id} for session {session_id} not found, creating new one")
                pass
        
        # Create new container
        container_id = self.create_container()
        self.session_container_map[session_id] = container_id
        logger.info(f"Created new container {container_id} for session {session_id}")
        return container_id
    
    def create_container(self) -> str:
        """Create a new Docker container and return its ID"""
        container_name = f"python-sandbox-{str(uuid.uuid4())[:8]}"
        
        try:
            # Create container with proper security constraints
            container = self.docker_client.containers.create(
                image=self.base_image,
                name=container_name,
                detach=True,
                volumes={str(RESULTS_DIR.absolute()): {'bind': '/app/results', 'mode': 'rw'}},
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
            
            # Start container
            container.start()
            
            container_id = container.id
            self.container_last_used[container_id] = datetime.now()
            logger.info(f"Created new container: {container_id} (name: {container_name})")
            return container_id
        except Exception as e:
            logger.error(f"Failed to create container: {e}", exc_info=True)
            raise
    
    def verify_container_exists(self, container_id: str) -> Optional[Dict[str, Any]]:
        """Verify container exists and clean up if not. Returns error dict if not exists."""
        if container_id not in self.container_last_used:
            return {"error": f"Container {container_id} does not exist or was cleaned up. Please create a new one using create_python_env."}
        
        try:
            self.docker_client.containers.get(container_id)
            # Update last used time
            self.container_last_used[container_id] = datetime.now()
            return None
        except docker.errors.NotFound:
            # Clean up potentially stale records
            self._clean_stale_container_records(container_id)
            return {"error": f"Container {container_id} not found. Please create a new environment using create_python_env."}
    
    def _clean_stale_container_records(self, container_id: str) -> None:
        """Clean up stale container records"""
        if container_id in self.container_last_used:
            del self.container_last_used[container_id]
        sessions_to_remove = [sid for sid, cid in self.session_container_map.items() if cid == container_id]
        for session_id in sessions_to_remove:
            del self.session_container_map[session_id]
        
        # Clean up associated files
        cleanup_container_files(container_id)
        
        logger.warning(f"Container not found for known container_id {container_id}. Records cleaned.")
    
    @contextmanager
    def _get_running_container(self, container_id: str):
        """Context manager to get a running container, with auto-restart if needed"""
        try:
            container = self.docker_client.containers.get(container_id)
            
            # Ensure container is running
            if container.status != "running":
                logger.info(f"Container {container_id} is not running. Current status: {container.status}")
                
                # If container status is exited, try to get container logs to understand why
                if container.status == "exited":
                    try:
                        logs = container.logs().decode('utf-8', errors='replace')
                        logger.warning(f"Container {container_id} exited. Container logs: {logs}")
                    except Exception as log_err:
                        logger.error(f"Failed to get logs for exited container {container_id}: {log_err}")
                
                # Try to start the container
                logger.info(f"Attempting to start container {container_id}...")
                container.start()
                container.reload()
                logger.info(f"Container {container_id} started successfully.")
            
            yield container
            
        except docker.errors.NotFound:
            logger.error(f"Container {container_id} not found during operation.")
            self._clean_stale_container_records(container_id)
            raise ValueError(f"Container {container_id} not found.")
    
    def execute_python_code(self, container_id: str, code: str) -> Dict[str, Any]:
        """Execute Python code in a Docker container"""
        # Verify container exists
        error = self.verify_container_exists(container_id)
        if error:
            return error
        
        # Force check and delete expired files before execution
        check_and_delete_files()
        
        # Log execution details
        logger.info("Executing code:")
        logger.info("=" * 50)
        logger.info(code)
        logger.info("=" * 50)
        logger.info(f"Running code in container {container_id}")
        
        try:
            with self._get_running_container(container_id) as container:
                # Write Python code to a temporary file, then execute that file in the container
                # This avoids issues with quotes and special characters in command line
                temp_code_file = "/tmp/code_to_run.py"
                
                # 1. Write the code to a temporary file inside the container
                write_code_cmd = f"cat > {temp_code_file} << 'EOL'\n{code}\nEOL"
                write_result = container.exec_run(
                    cmd=["sh", "-c", write_code_cmd],
                    workdir="/app/results",
                    privileged=False
                )
                
                if write_result.exit_code != 0:
                    logger.error(f"Failed to write code to container: {write_result.output.decode('utf-8')}")
                    return {
                        "error": "Failed to prepare code execution",
                        "stdout": "",
                        "stderr": write_result.output.decode('utf-8'),
                        "exit_code": write_result.exit_code,
                        "files": [],
                        "file_links": []
                    }
                
                # 2. Execute the code from the temporary file
                exec_result = container.exec_run(
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
                container.exec_run(
                    cmd=["rm", "-f", temp_code_file],
                    privileged=False
                )
                
                # Log execution results
                logger.info("Execution results:")
                logger.info(f"Exit code: {exit_code}")
                if stdout:
                    logger.info("Stdout:")
                    logger.info(stdout)
                if stderr:
                    logger.warning("Stderr:")
                    logger.warning(stderr)
                
                # Collect output files - pass container_id for file safety
                files, file_links = collect_output_files(container_id, self.container_last_used)
                
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "files": files,
                    "file_links": file_links
                }
        except ValueError as e:
            # Container not found error from context manager
            return {
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "files": [],
                "file_links": []
            }
        except Exception as e:
            logger.error(f"Failed to run code in container {container_id}: {e}", exc_info=True)
            
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
    
    def _install_package_async(self, container_id: str, package_name: str) -> None:
        """Asynchronously install package and update status"""
        try:
            status_key = f"{container_id}:{package_name}"
            self.package_install_status[status_key] = {
                "status": "installing",
                "start_time": datetime.now(),
                "message": f"Installing {package_name}...",
                "complete": False
            }

            with self._get_running_container(container_id) as container:
                # Execute pip install command
                exec_result = container.exec_run(
                    cmd=f"pip install {package_name}",
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
                    self.package_install_status[status_key] = {
                        "status": "success",
                        "message": f"Successfully installed {package_name}",
                        "complete": True,
                        "success": True,
                        "end_time": datetime.now()
                    }
                else:
                    self.package_install_status[status_key] = {
                        "status": "failed",
                        "message": f"Failed to install {package_name}: {output}",
                        "stderr": output,
                        "complete": True,
                        "success": False,
                        "end_time": datetime.now()
                    }
        except Exception as e:
            logger.error(f"Failed to install package {package_name} for container {container_id}: {e}", exc_info=True)
            
            # Get more detailed error information
            error_message = str(e)
            if hasattr(e, 'stderr') and e.stderr:
                stderr = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
                error_message = f"{error_message}\nDetails: {stderr}"
            
            status_key = f"{container_id}:{package_name}"
            self.package_install_status[status_key] = {
                "status": "failed",
                "message": f"Error: {error_message}",
                "stderr": error_message,
                "complete": True,
                "success": False,
                "end_time": datetime.now()
            }
    
    def install_package(self, container_id: str, package_name: str) -> Dict[str, Any]:
        """Asynchronously install package and return status immediately"""
        # Verify container exists
        error = self.verify_container_exists(container_id)
        if error:
            return error
        
        logger.info(f"Starting async installation of package {package_name} for container {container_id}")
        status_key = f"{container_id}:{package_name}"
        
        # Check if already installing
        if status_key in self.package_install_status:
            status = self.package_install_status[status_key]
            if status["status"] == "installing" and not status["complete"]:
                return {
                    "success": None,
                    "status": "installing",
                    "message": f"Package {package_name} installation already in progress"
                }
        
        # Start asynchronous installation thread
        install_thread = threading.Thread(
            target=self._install_package_async,
            args=(container_id, package_name),
            daemon=True
        )
        install_thread.start()
        
        # Return "installing" status immediately
        return {
            "success": None,
            "status": "installing",
            "message": f"Started installation of {package_name}. Use check_package_status to monitor progress."
        }
    
    def check_package_status(self, container_id: str, package_name: str) -> Dict[str, Any]:
        """Check the installation status of a package"""
        # Verify container exists
        error = self.verify_container_exists(container_id)
        if error:
            return error
        
        status_key = f"{container_id}:{package_name}"
        
        # If no installation record found
        if status_key not in self.package_install_status:
            # Check if package is already installed (might have been installed without tracking)
            try:
                with self._get_running_container(container_id) as container:
                    # Use pip list and filter results to check if package is installed
                    exec_result = container.exec_run(
                        cmd=f"pip list | grep -i {package_name}",
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
        if status["status"] == "installing" and not status["complete"]:
            elapsed_time = datetime.now() - status["start_time"]
            status["elapsed_seconds"] = elapsed_time.total_seconds()
        
        return status
    
    def cleanup_old_containers(self) -> int:
        """Clean up containers that haven't been used for specified time, return number of cleaned containers"""
        cutoff_time = datetime.now() - timedelta(hours=self.cleanup_after_hours)
        containers_to_remove = [container_id for container_id, last_used in self.container_last_used.items() 
                              if last_used < cutoff_time]
        
        for container_id in containers_to_remove:
            try:
                container = self.docker_client.containers.get(container_id)
                # Stop and remove container
                container.stop(timeout=5)
                container.remove(force=True)
                logger.info(f"Cleaned up inactive container: {container_id}")
            except docker.errors.NotFound:
                logger.info(f"Container {container_id} already removed")
            except Exception as e:
                logger.error(f"Failed to clean up container {container_id}: {e}")
            
            # Clean up records and associated files
            self._clean_stale_container_records(container_id)
        
        return len(containers_to_remove) 