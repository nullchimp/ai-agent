"""
File operations module for secure file handling.
"""
from typing import List
import os
import pathlib


class FileService:
    """
    Service for handling file operations within a secure base directory.
    """
    
    def __init__(self, base_dir: str):
        """
        Initialize a FileService with a base directory.
        
        Args:
            base_dir: The base directory for all file operations
            
        Raises:
            ValueError: If the base directory cannot be created or accessed
        """
        # Ensure the base directory exists
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir, mode=0o755, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Failed to create base directory: {str(e)}")
        
        # Convert to absolute path
        self.base_dir = os.path.abspath(base_dir)
    
    def write_to_file(self, filename: str, content: str) -> None:
        """
        Writes content to a file within the base directory.
        
        Args:
            filename: The relative path of the file to write
            content: The content to write to the file
            
        Raises:
            ValueError: If the path is invalid or writing fails
            IOError: If file operations fail
        """
        # Ensure the file path doesn't escape the base directory
        full_path = self._get_secure_path(filename)
        
        # Make sure target directory exists
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, mode=0o755, exist_ok=True)
        
        # Write the file
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except IOError as e:
            raise ValueError(f"Failed to write file: {str(e)}")
    
    def read_file(self, filename: str) -> str:
        """
        Reads content from a file within the base directory.
        
        Args:
            filename: The relative path of the file to read
            
        Returns:
            The file contents as a string
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the path is invalid
            IOError: If file operations fail
        """
        # Ensure the file path doesn't escape the base directory
        full_path = self._get_secure_path(filename)
        
        # Check if file exists
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"File not found: {filename}")
        
        # Read the file
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            raise ValueError(f"Failed to read file: {str(e)}")
    
    def list_files(self, directory: str) -> List[str]:
        """
        Lists files in the given directory within the base directory.
        
        Args:
            directory: The relative path of the directory to list
            
        Returns:
            A list of filenames in the directory
            
        Raises:
            FileNotFoundError: If the directory doesn't exist
            ValueError: If the path is invalid
            IOError: If directory operations fail
        """
        # Ensure the directory path doesn't escape the base directory
        full_path = self._get_secure_path(directory)
        
        # Check if directory exists
        if not os.path.isdir(full_path):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Read directory
        try:
            return os.listdir(full_path)
        except IOError as e:
            raise ValueError(f"Failed to list directory: {str(e)}")
    
    def _get_secure_path(self, requested_path: str) -> str:
        """
        Ensures the requested path doesn't escape the base directory.
        
        Args:
            requested_path: The requested path relative to base directory
            
        Returns:
            The full, secure path within the base directory
            
        Raises:
            ValueError: If the path is invalid or attempts directory traversal
        """
        # Clean the path to normalize it
        clean_path = os.path.normpath(requested_path)
        
        # Reject absolute paths
        if os.path.isabs(clean_path):
            raise ValueError("Absolute paths not allowed")
        
        # Join with base directory
        full_path = os.path.join(self.base_dir, clean_path)
        
        # Make sure the result is still within the base directory
        abs_path = os.path.abspath(full_path)
        
        # Check if the path is within the base directory
        if not abs_path.startswith(self.base_dir):
            # If path tries to escape, rewrite it to be inside base directory
            # by just using the filename component
            filename = os.path.basename(clean_path)
            full_path = os.path.join(self.base_dir, filename)
        
        return full_path