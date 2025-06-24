from . import Tool
from typing import Optional

class ListFiles(Tool):
    @property
    def name(self) -> str:
        return "list_files"
    
    @property
    def description(self) -> str:
        return "List files and directories within a specified directory path, constrained to operate within a secure base directory for security. Returns comprehensive file listing with metadata including file names, types, and directory structure. Supports recursive directory traversal within security boundaries."
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "Absolute path to the base directory that serves as the security boundary for all file operations. All file access is restricted to this directory and its subdirectories."
                },
                "directory": {
                    "type": "string",
                    "description": "Relative path to the subdirectory within base_dir to list files from. Defaults to '.' for current directory. Path traversal attacks are prevented by security validation."
                }
            },
            "required": ["base_dir"]
        }
    
    async def run(self, base_dir: str, directory: Optional[str] = "."):
        from libs.fileops.file import FileService
        
        service = FileService(base_dir)
        try:
            files = service.list_files(directory)
            return {
                "success": True,
                "result": f"Successfully listed files in {directory}",
                "base_dir": base_dir,
                "directory": directory,
                "files": files
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"Failed to list files: {str(e)}",
                "base_dir": base_dir,
                "directory": directory,
                "files": []
            }