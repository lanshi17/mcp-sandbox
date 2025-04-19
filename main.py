import uvicorn
from fastapi import FastAPI
from mcp_sandbox.utils.task_manager import PeriodicTaskManager
from mcp_sandbox.utils.file_manager import check_and_delete_files, cleanup_results_directory
from mcp_sandbox.core.python_service import PythonExecutionService
from mcp_sandbox.api.routes import configure_app
from mcp_sandbox.utils.config import logger, RESULTS_DIR, HOST, PORT

# Initialize service at module level
service = PythonExecutionService()
mcp = service.mcp  # Doing this allows fastmcp to find the MCP object 
docker_manager = service.docker_manager

def main():
    """Main entry point for the application"""
    # Create FastAPI app
    app = FastAPI(title="Python Docker Executor")
    
    # Configure app routes and middlewares
    configure_app(app, mcp._mcp_server)

    # Ensure RESULTS_DIR exists
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # Clean up results directory on startup
    cleanup_results_directory()

    # Start file cleanup task
    PeriodicTaskManager.start_file_cleanup(check_and_delete_files)
    
    # Start container cleanup task
    PeriodicTaskManager.start_task(docker_manager.cleanup_old_containers, 3600, "container cleanup")

    # Start FastAPI server
    logger.info("Starting Python Docker Executor service")
    logger.info(f"Using Docker base image: {docker_manager.base_image}")
    logger.info(f"Using results directory: {RESULTS_DIR}")
    
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main() 