from typing import Dict, Any
from fastmcp import FastMCP

from mcp_sandbox.core.docker_manager import DockerManager
from mcp_sandbox.utils.config import DEFAULT_DOCKER_IMAGE

class MCPTools:
    """A set of MCP tools for Python code execution using Docker containers"""
    
    def __init__(self, base_image: str = DEFAULT_DOCKER_IMAGE):
        self.docker_manager = DockerManager(base_image=base_image)
        self.mcp = FastMCP("Python Docker Executor 🐳")
        self._register_mcp_tools()
    
    def _register_mcp_tools(self):
        """Register all MCP tools"""
        
        @self.mcp.tool(
            name="create_python_env", 
            description="Creates a new Python Docker container and returns its ID for subsequent operations. No parameters required."
        )
        def create_python_env() -> str:
            """
            Create a new Python Docker container and return its ID
            
            The returned container ID can be used in subsequent execute_python_code and install_package_in_env calls
            The container will be automatically cleaned up after 1 hours of inactivity
            """
            return self.docker_manager.create_container()

        @self.mcp.tool(
            name="execute_python_code", 
            description="Executes Python code in a Docker container and returns results with links to generated files. Parameters: container_id (string) - The container ID to use, code (string) - The Python code to execute"
        )
        def execute_python_code(container_id: str, code: str) -> Dict[str, Any]:
            """
            Run code in a Python Docker container with specified ID
            
            Parameters:
            - container_id: ID of the container created by create_python_env
            - code: The Python code to execute
            
            Returns a dictionary with execution results and links to generated files
            """
            return self.docker_manager.execute_code(container_id, code)

        @self.mcp.tool(
            name="install_package_in_env",
            description="Installs a Python package in the specified Docker container. Parameters: container_id (string), package_name (string)"
        )
        def install_package_in_env(container_id: str, package_name: str) -> Dict[str, Any]:
            """
            Install a Python package in a Docker container
            
            Parameters:
            - container_id: ID of the container created by create_python_env
            - package_name: Name of the package to install
            
            Returns the installation status and logs
            """
            return self.docker_manager.install_package(container_id, package_name)

        @self.mcp.tool(
            name="check_package_status",
            description="Checks the installation status of a package in a Docker container. Parameters: container_id (string), package_name (string)"
        )
        def check_package_status(container_id: str, package_name: str) -> Dict[str, Any]:
            """
            Check the installation status of a package in a Python Docker container
            
            Parameters:
            - container_id: ID of the container created by create_python_env
            - package_name: Name of the package to check
            
            Returns the current status of the package installation (success, installing, failed)
            """
            return self.docker_manager.check_package_status(container_id, package_name)
