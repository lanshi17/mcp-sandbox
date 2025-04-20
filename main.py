import uvicorn
from fastapi import FastAPI
from mcp_sandbox.core.mcp_tools import MCPTools
from mcp_sandbox.api.routes import configure_app
from mcp_sandbox.utils.config import logger, HOST, PORT

# Initialize service at module level
mcp_tools = MCPTools()
mcp_server = mcp_tools.mcp
mcp = mcp_server._mcp_server # for fastmcp command to recognize

def main():
    """Main entry point for the application"""
    # Create FastAPI app
    app = FastAPI(title="Python Docker Executor")
    
    # Configure app routes and middlewares
    configure_app(app, mcp_server._mcp_server)

    # Start FastAPI server
    logger.info("Starting MCP Sandbox")
    
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main() 