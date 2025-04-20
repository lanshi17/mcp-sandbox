from typing import Dict, Any
from fastmcp import FastMCP

from mcp_sandbox.core.docker_manager import DockerManager
from mcp_sandbox.utils.config import DEFAULT_DOCKER_IMAGE

class MCPTools:
    """A set of MCP tools for Python code execution using Docker containers"""
    
    def __init__(self, base_image: str = DEFAULT_DOCKER_IMAGE):
        self.docker_manager = DockerManager(base_image=base_image)
        self.mcp = FastMCP("Python Docker Executor ")
        self._register_mcp_tools()
    
    def _register_mcp_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool(
            name="list_sandboxes",
            description="Lists all existing Python Docker sandboxes and their status. Each item also includes installed Python packages."
        )
        def list_sandboxes() -> list:
            """
            Return a list of all existing Python Docker sandboxes managed by this service.
            Each item includes sandbox_id, status, image, created, last_used, and a list of installed packages.
            """
            sandboxes = self.docker_manager.list_sandboxes()
            # For each sandbox, get installed packages
            for sandbox in sandboxes:
                sandbox["installed_packages"] = self.docker_manager.list_installed_packages(sandbox["sandbox_id"])
            return sandboxes

        
        @self.mcp.tool(
            name="create_sandbox", 
            description="Creates a new Python Docker sandbox and returns its ID for subsequent operations. No parameters required."
        )
        def create_sandbox() -> str:
            """
            Create a new Python Docker sandbox and return its ID
            
            The returned sandbox ID can be used in subsequent execute_python_code and install_package_in_sandbox calls
            The sandbox will be automatically cleaned up after 1 hours of inactivity
            """
            return self.docker_manager.create_sandbox()

        @self.mcp.tool(
            name="install_package_in_sandbox",
            description="Installs a Python package in the specified Docker sandbox. Parameters: sandbox_id (string), package_name (string)"
        )
        def install_package_in_sandbox(sandbox_id: str, package_name: str) -> Dict[str, Any]:
            """
            Install a Python package in a Docker sandbox
            
            Parameters:
            - sandbox_id: ID of the sandbox created by create_sandbox
            - package_name: Name of the package to install
            
            Returns the installation status and logs
            """
            return self.docker_manager.install_package(sandbox_id, package_name)

        @self.mcp.tool(
            name="check_package_installation_status",
            description="Checks the installation status of a package in a Docker sandbox. Parameters: sandbox_id (string), package_name (string)"
        )
        def check_package_installation_status(sandbox_id: str, package_name: str) -> Dict[str, Any]:
            """
            Check the installation status of a package in a Python Docker sandbox
            
            Parameters:
            - sandbox_id: ID of the sandbox created by create_sandbox
            - package_name: Name of the package to check
            
            Returns the current status of the package installation (success, installing, failed)
            """
            return self.docker_manager.check_package_status(sandbox_id, package_name)

        @self.mcp.tool(
            name="execute_python_code", 
            description="Executes Python code in a Docker sandbox and returns results with links to generated files. Parameters: sandbox_id (string) - The sandbox ID to use, code (string) - The Python code to execute"
        )
        def execute_python_code(sandbox_id: str, code: str) -> Dict[str, Any]:
            """
            Run code in a Python Docker sandbox with specified ID
            
            Parameters:
            - sandbox_id: ID of the sandbox created by create_sandbox
            - code: The Python code to execute
            
            Returns a dictionary with execution results and links to generated files
            """
            return self.docker_manager.execute_python_code(sandbox_id, code)


        @self.mcp.tool(
            name="execute_terminal_command",
            description="Executes a terminal command in the specified Docker sandbox. Parameters: sandbox_id (string), command (string). Returns stdout, stderr, exit_code."
        )
        def execute_terminal_command(sandbox_id: str, command: str) -> Dict[str, Any]:
            """
            Execute a shell command in the specified Docker sandbox.

            Parameters:
            - sandbox_id: ID of the sandbox created by create_sandbox
            - command: The shell command to execute

            Returns a dictionary with stdout, stderr, and exit_code
            """
            try:
                with self.docker_manager._get_running_sandbox(sandbox_id) as sandbox:
                    exec_result = sandbox.exec_run(command, stdout=True, stderr=True, stdin=False, tty=False)
                    return {
                        "stdout": exec_result.output.decode(errors="replace") if exec_result.output else "",
                        "stderr": "",
                        "exit_code": exec_result.exit_code
                    }
            except Exception as e:
                return {
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1
                }

        @self.mcp.tool(
            name="upload_file_to_sandbox",
            description="Uploads a local file to the specified Docker sandbox. Parameters: sandbox_id (string), local_file_path (string), dest_path (string, optional, default: /app/results)."
        )
        def upload_file_to_sandbox(sandbox_id: str, local_file_path: str, dest_path: str = "/app/results") -> dict:
            """
            Upload a local file to the specified path inside the sandbox.

            Parameters:
            - sandbox_id: ID of the sandbox created by create_sandbox
            - local_file_path: Path to the local file to upload
            - dest_path: Destination directory in the sandbox (default: /app/results)

            Returns a dict indicating success or error.
            """
            return self.docker_manager.upload_file_to_sandbox(sandbox_id, local_file_path, dest_path)
