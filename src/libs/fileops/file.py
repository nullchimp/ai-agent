"""
File operations module for secure file handling.
"""
from typing import List
import os


class FileService:
    """
    Service for handling file operations within a secure base directory.
    """
    
    def __init__(self, base_dir: str):
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir, mode=0o755, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Failed to create base directory: {str(e)}")
        
        self.base_dir = os.path.abspath(base_dir)
    
    def write_to_file(self, filename: str, content: str) -> None:
        full_path = self._get_secure_path(filename)
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, mode=0o755, exist_ok=True)
        
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except IOError as e:
            raise ValueError(f"Failed to write file: {str(e)}")
    
    def read_file(self, filename: str) -> str:
        full_path = self._get_secure_path(filename)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"File not found: {filename}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            raise ValueError(f"Failed to read file: {str(e)}")
    
    def list_files(self, directory: str) -> List[str]:
        full_path = self._get_secure_path(directory)
        if not os.path.isdir(full_path):
            raise FileNotFoundError(f"Directory not found: {directory}")

        try:
            return os.listdir(full_path)
        except IOError as e:
            raise ValueError(f"Failed to list directory: {str(e)}")
    
    def _get_secure_path(self, requested_path: str) -> str:
        clean_path = os.path.normpath(requested_path)
        if os.path.isabs(clean_path):
            raise ValueError("Absolute paths not allowed")

        full_path = os.path.join(self.base_dir, clean_path)
        abs_path = os.path.abspath(full_path)

        if not abs_path.startswith(self.base_dir):
            filename = os.path.basename(clean_path)
            full_path = os.path.join(self.base_dir, filename)
        
        return full_path