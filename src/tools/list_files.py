from . import Tool
from typing import Optional

class ListFiles(Tool):
    def define(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files within a secure base directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "base_dir": {
                            "type": "string",
                            "description": "Base directory for file operations"
                        },
                        "directory": {
                            "type": "string",
                            "description": "The relative subdirectory path to list files from (default: '.')"
                        }
                    },
                    "required": ["base_dir"]
                }
            }
        }
    
    async def run(self, base_dir: str, directory: Optional[str] = "."):
        from libs.fileops.file import FileService
        
        service = FileService(base_dir)
        try:
            files = service.list_files(directory)
            return {
                "success": True,
                "message": f"Successfully listed files in {directory}",
                "base_dir": base_dir,
                "directory": directory,
                "files": files
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to list files: {str(e)}",
                "base_dir": base_dir,
                "directory": directory,
                "files": []
            }