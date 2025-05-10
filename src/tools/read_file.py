from . import Tool

class ReadFile(Tool):
    def define(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read content from a file within a secure base directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "base_dir": {
                            "type": "string",
                            "description": "Base directory for file operations"
                        },
                        "filename": {
                            "type": "string",
                            "description": "The name of the file to read from (relative path)"
                        }
                    },
                    "required": ["base_dir", "filename"]
                }
            }
        }
    
    async def run(self, base_dir: str, filename: str):
        from libs.fileops.file import FileService
        
        service = FileService(base_dir)
        try:
            content = service.read_file(filename)
            return {
                "success": True,
                "message": f"Successfully read content from {filename}",
                "filename": filename,
                "base_dir": base_dir,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to read file: {str(e)}",
                "filename": filename,
                "base_dir": base_dir,
                "content": None
            }