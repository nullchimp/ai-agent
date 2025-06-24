from . import Tool

class ReadFile(Tool):
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read and return the complete content of a specified file within security-constrained base directory boundaries. Supports text and binary file reading with proper error handling for missing files, permission issues, and encoding problems. File access is restricted to the specified base directory to prevent path traversal vulnerabilities."
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "Absolute path to the base directory that serves as the security boundary for all file operations. All file access is restricted to this directory and its subdirectories."
                },
                "filename": {
                    "type": "string",
                    "description": "Relative path to the target file within base_dir. Can include subdirectory paths. Path traversal attempts (../) are automatically prevented by security validation."
                }
            },
            "required": ["base_dir", "filename"]
        }
    
    async def run(self, base_dir: str, filename: str):
        from libs.fileops.file import FileService
        
        service = FileService(base_dir)
        try:
            content = service.read_file(filename)
            return {
                "success": True,
                "result": f"Successfully read content from {filename}",
                "filename": filename,
                "base_dir": base_dir,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"Failed to read file: {str(e)}",
                "filename": filename,
                "base_dir": base_dir,
                "content": None
            }