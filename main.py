import uvicorn
from fastapi import FastAPI
from mcp_sandbox.core.mcp_tools import SandboxToolsPlugin
from mcp_sandbox.api.routes import configure_app
from mcp_sandbox.utils.config import logger, HOST, PORT


def main():
    """Main entry point for the application"""
    # Create FastAPI app
    app = FastAPI(title="Python Docker Executor")

    # Initialize sandbox tools
    sandbox_plugin = SandboxToolsPlugin()
    mcp_server = sandbox_plugin.mcp
    
    # Configure app routes and middlewares
    configure_app(app, mcp_server._mcp_server)

    # Start FastAPI server
    logger.info("Starting MCP Sandbox")
    
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main() 