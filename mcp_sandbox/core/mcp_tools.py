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
            name="create_sandbox", 
            description="Creates a new Python Docker sandbox and returns its ID for subsequent operations. No parameters required."
        )
        def create_sandbox() -> str:
            """
            Create a new Python Docker sandbox and return its ID
            
            The returned sandbox ID can be used in subsequent execute_python_code and install_package_in_sandbox calls
            The sandbox will be automatically cleaned up after 1 hours of inactivity
            """
            return self.docker_manager.create_container()

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
            name="check_package_status",
            description="Checks the installation status of a package in a Docker sandbox. Parameters: sandbox_id (string), package_name (string)"
        )
        def check_package_status(sandbox_id: str, package_name: str) -> Dict[str, Any]:
            """
            Check the installation status of a package in a Python Docker sandbox
            
            Parameters:
            - sandbox_id: ID of the sandbox created by create_sandbox
            - package_name: Name of the package to check
            
            Returns the current status of the package installation (success, installing, failed)
            """
            return self.docker_manager.check_package_status(sandbox_id, package_name)

        @self.mcp.tool(
            name="list_sandboxes",
            description="Lists all existing Python Docker sandboxes and their status. Each item also includes installed Python packages."
        )
        def list_sandboxes() -> list:
            """
            Return a list of all existing Python Docker sandboxes managed by this service.
            Each item includes sandbox_id, status, image, created, last_used, and a list of installed packages.
            """
            sandboxes = self.docker_manager.list_containers()
            # For each sandbox, get installed packages
            for sandbox in sandboxes:
                sandbox["installed_packages"] = self.docker_manager.list_installed_packages(sandbox["sandbox_id"])
            return sandboxes
