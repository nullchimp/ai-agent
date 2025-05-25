from . import Tool
from typing import Optional

class ListFiles(Tool):
    @property
    def name(self) -> str:
        return "list_files"
    
    @property
    def description(self) -> str:
        return "List files in a specified directory within a secure base directory."
    
    @property
    def parameters(self) -> dict:
        return {
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