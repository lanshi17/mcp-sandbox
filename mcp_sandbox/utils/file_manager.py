from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict
import shutil
import re

from mcp_sandbox.utils.config import logger, RESULTS_DIR, BASE_URL

# Dictionary to store accessed files for delayed deletion
files_to_delete = {}

# Dictionary to map files to their container IDs
file_container_map = {}

def cleanup_results_directory() -> None:
    """Clean up all files in the results directory on startup"""
    try:
        # Ensure directory exists
        RESULTS_DIR.mkdir(exist_ok=True)
        
        # Remove all files in the directory
        count = 0
        for file in RESULTS_DIR.glob("*"):
            if file.is_file():
                try:
                    file.unlink()
                    count += 1
                except Exception as e:
                    logger.error(f"Error deleting file {file.name}: {e}")
        
        # Clear tracking dictionaries
        files_to_delete.clear()
        file_container_map.clear()
        
        logger.info(f"Cleaned up {count} files from results directory on startup")
    except Exception as e:
        logger.error(f"Error cleaning up results directory: {e}")

def schedule_file_deletion(file_path: Path, hours: int = 1, container_id: Optional[str] = None) -> None:
    """Schedule a file for deletion after specified hours"""
    if file_path.exists() and file_path.is_file():
        delete_time = datetime.now() + timedelta(hours=hours)
        files_to_delete[str(file_path)] = delete_time
        
        # Store container association if provided
        if container_id:
            file_container_map[str(file_path)] = container_id
            
        logger.info(f"Scheduled file deletion at {delete_time.strftime('%Y-%m-%d %H:%M:%S')} for: {file_path.name}")

def generate_safe_filename(base_name: str, container_id: str) -> str:
    """Generate a safe filename with container ID and timestamp"""
    container_short_id = container_id[:8] if container_id else "unknown"
    
    # Extract extension if present
    name_parts = base_name.split('.')
    
    has_timestamp = False
    timestamp_part = ""
    
    base_parts = name_parts[0].split('_')
    
    base_without_ids = base_parts[0]
    
    for part in base_parts[1:]:
        if re.match(r'\d{8}_\d{6}', part):
            has_timestamp = True
            timestamp_part = part
            break
    
    if not has_timestamp:
        timestamp_part = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 构建新文件名
    if len(name_parts) > 1:
        ext = name_parts[-1]
        return f"{base_without_ids}_{container_short_id}_{timestamp_part}.{ext}"
    else:
        return f"{base_without_ids}_{container_short_id}_{timestamp_part}"

def cleanup_container_files(container_id: str) -> None:
    """Clean up files associated with a specific container"""
    files_to_remove = [file_path for file_path, cid in file_container_map.items() 
                     if cid == container_id]
    
    for file_path_str in files_to_remove:
        file_path = Path(file_path_str)
        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
                logger.info(f"Deleted file for container {container_id}: {file_path.name}")
            except Exception as e:
                logger.error(f"Error deleting file: {e}")
        
        # Remove from maps
        file_container_map.pop(file_path_str, None)
        files_to_delete.pop(file_path_str, None)

def check_and_delete_files() -> None:
    """Check and delete files scheduled for deletion"""
    current_time = datetime.now()
    files_to_remove = []
    
    for file_path_str, delete_time in files_to_delete.items():
        if current_time >= delete_time:
            file_path = Path(file_path_str)
            if file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                    logger.info(f"Deleted scheduled file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Error deleting file: {e}")
            files_to_remove.append(file_path_str)
    
    # Remove processed files from dictionary
    for file_path in files_to_remove:
        files_to_delete.pop(file_path, None)
        file_container_map.pop(file_path, None)

def collect_output_files(container_id: str, container_last_used: Dict[str, datetime]) -> Tuple[List[str], List[Dict[str, str]]]:
    """Collect generated files and create links"""
    file_links = []
    files = []
    
    # Get container short ID for file identification
    container_short_id = container_id[:8] if container_id else "unknown"
    
    for file in RESULTS_DIR.glob("*"):
        if file.is_file():
            file_name = file.name
            current_path = file
            
            # Check if file already has a container ID
            # 1. If filename contains any container ID, keep original name
            # 2. Only files without any container ID need current container ID and renaming
            
            # Check if file contains any known container ID
            has_container_id = any(cid[:8] in file_name for cid in container_last_used.keys())
            
            # If file already has current container ID, consider it as current container file
            is_current_container_file = container_short_id in file_name
            
            # If file is new or belongs to current container, process it
            is_new_file = not has_container_id
            
            if is_new_file or is_current_container_file:
                # Only new files (no container ID) need renaming
                if is_new_file and not is_current_container_file:
                    # Create a safe file with container ID
                    safe_name = generate_safe_filename(file_name, container_id)
                    new_path = RESULTS_DIR / safe_name
                    
                    # Rename the file
                    try:
                        shutil.move(str(file), str(new_path))
                        logger.info(f"Renamed file {file_name} to {safe_name}")
                        file_name = safe_name
                        current_path = new_path
                        
                        # Map file to container
                        file_container_map[str(new_path)] = container_id
                    except Exception as e:
                        logger.error(f"Failed to rename file {file_name}: {e}")
                
                # Schedule deletion for all files (renamed or not)
                if str(current_path) not in files_to_delete:
                    schedule_file_deletion(current_path, hours=1, container_id=container_id)
                    logger.info(f"Scheduled deletion for file: {file_name}")
                
                files.append(file_name)
                file_url = f"{BASE_URL}{file_name}"
                file_links.append({"name": file_name, "url": file_url})
    
    return files, file_links 