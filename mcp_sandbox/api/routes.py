from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from mcp.server.sse import SseServerTransport

from mcp_sandbox.utils.config import logger, RESULTS_DIR

def configure_app(app: FastAPI, mcp_server):
    """Configure FastAPI app with routes and middleware"""
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(RESULTS_DIR)), name="static")

    # SSE handling
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        """Handle SSE connections"""
        # Set up initialization options
        initialization_options = mcp_server.create_initialization_options()
        
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                initialization_options,
            )

    # Add SSE routes
    app.add_route("/sse", handle_sse)
    app.mount("/messages/", app=sse.handle_post_message)

    # File access middleware
    @app.middleware("http")
    async def track_file_access(request: Request, call_next):
        """Middleware to track file access"""
        response = await call_next(request)
        
        if request.url.path.startswith("/static/"):
            file_name = request.url.path.split("/")[-1]
            if file_name:
                logger.info(f"File accessed: {file_name}")
        
        return response
    
    return sse 