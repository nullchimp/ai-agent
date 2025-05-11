from . import Tool

class WriteFile(Tool):
    def define(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": f"{self.name}",
                "description": "Write content to a file within a secure base directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "base_dir": {
                            "type": "string",
                            "description": "Base directory for file operations"
                        },
                        "filename": {
                            "type": "string",
                            "description": "The name of the file to write to (relative path)"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content to write to the file"
                        }
                    },
                    "required": ["base_dir", "filename", "content"]
                }
            }
        }
    
    async def run(self, base_dir: str, filename: str, content: str):
        from libs.fileops.file import FileService
        
        service = FileService(base_dir)
        try:
            service.write_to_file(filename, content)
            return {
                "success": True,
                "message": f"Successfully wrote content to {filename} in {base_dir}",
                "filename": filename,
                "base_dir": base_dir
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to write to file: {str(e)}",
                "filename": filename,
                "base_dir": base_dir
            }