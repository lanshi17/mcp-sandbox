from typing import Dict, Any
from fastmcp import FastMCP
from mcp_sandbox.core.sandbox_modules.manager import SandboxManager
from mcp_sandbox.core.sandbox_modules.file_ops import SandboxFileOpsMixin
from mcp_sandbox.core.sandbox_modules.package import SandboxPackageMixin
from mcp_sandbox.core.sandbox_modules.records import SandboxRecordsMixin
from mcp_sandbox.core.sandbox_modules.execution import SandboxExecutionMixin
from mcp_sandbox.utils.config import DEFAULT_DOCKER_IMAGE

class MCPToolsSandbox(
    SandboxManager, SandboxFileOpsMixin, SandboxPackageMixin, SandboxRecordsMixin, SandboxExecutionMixin
):
    pass

class MCPTools:
    """A set of MCP tools for Python code execution using Sandboxes"""
    
    def __init__(self, base_image: str = DEFAULT_DOCKER_IMAGE):
        self.sandbox_manager = MCPToolsSandbox(base_image=base_image)
        self.mcp = FastMCP("Python Sandbox Executor ")
        self._register_mcp_tools()
    
    def _register_mcp_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool(
            name="list_sandboxes",
            description="Lists all existing Python sandboxes and their status. Each item also includes installed Python packages."
        )
        def list_sandboxes() -> list:
            sandboxes = self.sandbox_manager.list_sandboxes()
            for sandbox in sandboxes:
                sandbox["installed_packages"] = self.sandbox_manager.list_installed_packages(sandbox["sandbox_id"])
            return sandboxes

        @self.mcp.tool(
            name="create_sandbox", 
            description="Creates a new Python sandbox and returns its ID for subsequent operations. No parameters required."
        )
        def create_sandbox() -> str:
            return self.sandbox_manager.create_sandbox()

        @self.mcp.tool(
            name="install_package_in_sandbox",
            description="Installs a Python package in the specified sandbox. Parameters: sandbox_id (string), package_name (string)"
        )
        def install_package_in_sandbox(sandbox_id: str, package_name: str) -> Dict[str, Any]:
            return self.sandbox_manager.install_package(sandbox_id, package_name)

        @self.mcp.tool(
            name="check_package_installation_status",
            description="Checks the installation status of a package in a sandbox. Parameters: sandbox_id (string), package_name (string)"
        )
        def check_package_installation_status(sandbox_id: str, package_name: str) -> Dict[str, Any]:
            return self.sandbox_manager.check_package_status(sandbox_id, package_name)

        @self.mcp.tool(
            name="execute_python_code", 
            description="Executes Python code in a sandbox and returns results with links to generated files. Parameters: sandbox_id (string) - The sandbox ID to use, code (string) - The Python code to execute"
        )
        def execute_python_code(sandbox_id: str, code: str) -> Dict[str, Any]:
            return self.sandbox_manager.execute_python_code(sandbox_id, code)

        @self.mcp.tool(
            name="execute_terminal_command",
            description="Executes a terminal command in the specified sandbox. Parameters: sandbox_id (string), command (string). Returns stdout, stderr, exit_code."
        )
        def execute_terminal_command(sandbox_id: str, command: str) -> Dict[str, Any]:
            try:
                with self.sandbox_manager._get_running_sandbox(sandbox_id) as sandbox:
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
            description="Uploads a local file to the specified sandbox. Parameters: sandbox_id (string), local_file_path (string), dest_path (string, optional, default: /app/results)."
        )
        def upload_file_to_sandbox(sandbox_id: str, local_file_path: str, dest_path: str = "/app/results") -> dict:
            return self.sandbox_manager.upload_file_to_sandbox(sandbox_id, local_file_path, dest_path)
