import os
from typing import Dict, List, Optional
import uuid
from datetime import datetime
import json
from pathlib import Path


class Database:
    """Simple file-based database for user authentication"""
    """Will be changed"""
    """Will be changed"""
    """Will be changed"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = Path(__file__).parent / "data"
        else:
            self.db_path = Path(db_path)
        
        self.users_path = self.db_path / "users.json"
        self.sandboxes_path = self.db_path / "sandboxes.json"
        
        # Initialize database files if they don't exist
        self._initialize_db()
    
    def _initialize_db(self):
        """Create database files if they don't exist"""
        os.makedirs(self.db_path, exist_ok=True)
        
        if not self.users_path.exists():
            with open(self.users_path, "w") as f:
                json.dump({}, f)
        
        if not self.sandboxes_path.exists():
            with open(self.sandboxes_path, "w") as f:
                json.dump({}, f)
    
    def get_user(self, username: str = None, email: str = None, user_id: str = None) -> Optional[Dict]:
        """Get user by username, email or ID"""
        try:
            with open(self.users_path, "r") as f:
                users = json.load(f)
            
            if username:
                # Case insensitive username check
                for uid, user_data in users.items():
                    if user_data.get("username", "").lower() == username.lower():
                        return {**user_data, "id": uid}
            
            if email:
                # Case insensitive email check
                for uid, user_data in users.items():
                    if user_data.get("email", "").lower() == email.lower():
                        return {**user_data, "id": uid}
            
            if user_id and user_id in users:
                return {**users[user_id], "id": user_id}
            
            return None
        except Exception as e:
            print(f"Error retrieving user: {e}")
            return None
    
    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user"""
        with open(self.users_path, "r") as f:
            users = json.load(f)
        
        user_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        new_user = {
            **user_data,
            "created_at": created_at,
            "is_active": True
        }
        
        users[user_id] = new_user
        
        with open(self.users_path, "w") as f:
            json.dump(users, f, indent=2)
        
        return {**new_user, "id": user_id}
    
    def update_user(self, user_id: str, user_data: Dict) -> Optional[Dict]:
        """Update a user"""
        with open(self.users_path, "r") as f:
            users = json.load(f)
        
        if user_id not in users:
            return None
        
        updated_user = {**users[user_id], **user_data}
        users[user_id] = updated_user
        
        with open(self.users_path, "w") as f:
            json.dump(users, f, indent=2)
        
        return {**updated_user, "id": user_id}
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        with open(self.users_path, "r") as f:
            users = json.load(f)
        
        return [{"id": user_id, **user_data} for user_id, user_data in users.items()]
    
    def create_sandbox(self, user_id: str, name: str = None, docker_container_id: str = None) -> str:
        """Create a new sandbox for a user"""
        with open(self.sandboxes_path, "r") as f:
            sandboxes = json.load(f)
        
        sandbox_id = str(uuid.uuid4())
        sandboxes[sandbox_id] = {
            "user_id": user_id,
            "name": name or f"Sandbox {len([s for s in sandboxes.values() if s.get('user_id') == user_id]) + 1}",
            "created_at": datetime.now().isoformat(),
            "docker_container_id": docker_container_id
        }
        
        with open(self.sandboxes_path, "w") as f:
            json.dump(sandboxes, f, indent=2)
        
        return sandbox_id
    
    def get_sandbox(self, sandbox_id: str) -> Optional[Dict]:
        """Get sandbox by ID"""
        try:
            with open(self.sandboxes_path, "r") as f:
                sandboxes = json.load(f)
            
            if sandbox_id in sandboxes:
                return {**sandboxes[sandbox_id], "id": sandbox_id}
            
            return None
        except Exception as e:
            print(f"Error retrieving sandbox: {e}")
            return None
    
    def get_user_sandboxes(self, user_id: str) -> List[Dict]:
        """Get all sandboxes for a user"""
        try:
            with open(self.sandboxes_path, "r") as f:
                sandboxes = json.load(f)
            
            user_sandboxes = []
            for sandbox_id, sandbox_data in sandboxes.items():
                if sandbox_data.get("user_id") == user_id:
                    user_sandboxes.append({**sandbox_data, "id": sandbox_id})
            
            return user_sandboxes
        except Exception as e:
            print(f"Error retrieving user sandboxes: {e}")
            return []
    
    def is_sandbox_owner(self, user_id: str, sandbox_id: str) -> bool:
        """Check if a user owns a sandbox"""
        sandbox = self.get_sandbox(sandbox_id)
        if not sandbox:
            return False
        
        return sandbox.get("user_id") == user_id
    
    def delete_sandbox(self, sandbox_id: str) -> bool:
        """Delete a sandbox by ID"""
        try:
            with open(self.sandboxes_path, "r") as f:
                sandboxes = json.load(f)
            
            if sandbox_id not in sandboxes:
                return False
            
            # Remove the sandbox from the database
            del sandboxes[sandbox_id]
            
            with open(self.sandboxes_path, "w") as f:
                json.dump(sandboxes, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error deleting sandbox: {e}")
            return False


# Create global instance
db = Database()
