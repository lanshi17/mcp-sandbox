from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from mcp_sandbox.core.docker_manager import DockerManager
from mcp_sandbox.utils.config import logger
import io
import os
import tarfile
import mimetypes

router = APIRouter()
docker_manager = DockerManager()

@router.get("/sandbox/file")
def get_container_file(
    container_id: str = Query(..., description="Docker container ID"),
    file_path: str = Query(..., description="Absolute path to the file inside the container, e.g. /app/results/foo.txt")
):
    """
    Read-only access to files inside a running Docker container.
    Returns the file content as a download if found.
    """
    try:
        container = docker_manager.docker_client.containers.get(container_id)
        stream, stat = container.get_archive(file_path)
        tar_bytes = io.BytesIO(b"".join(stream))
        with tarfile.open(fileobj=tar_bytes) as tar:
            # Locate correct member in tar archive
            members = tar.getmembers()
            if not members:
                raise HTTPException(status_code=404, detail="File not found in container")
            rel_path = file_path.lstrip("/")
            member = next((m for m in members if m.name == rel_path), None)
            if member is None:
                # Fallback to basename match
                basename = os.path.basename(file_path)
                member = next((m for m in members if m.name.endswith(basename)), members[0])
            fileobj = tar.extractfile(member)
            if not fileobj:
                raise HTTPException(status_code=404, detail="File not found in container")
            # Determine MIME type for inline display
            mime_type, _ = mimetypes.guess_type(member.name)
            mime_type = mime_type or "application/octet-stream"
            headers = {"Content-Disposition": f"inline; filename={member.name}"}
            return StreamingResponse(fileobj, media_type=mime_type, headers=headers)
    except Exception as e:
        logger.error(f"Failed to fetch file from container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching file from container: {e}")
