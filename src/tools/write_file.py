from . import Tool

class WriteFile(Tool):
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Write or overwrite content to a specified file within security-constrained base directory boundaries. Creates directories as needed and handles text encoding automatically. Supports creating new files or updating existing ones with comprehensive error handling for permission issues, disk space, and path validation. File operations are restricted to the specified base directory to prevent path traversal vulnerabilities."
    
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
                    "description": "Relative path to the target file within base_dir. Can include subdirectory paths which will be created if they don't exist. Path traversal attempts (../) are automatically prevented by security validation."
                },
                "content": {
                    "type": "string",
                    "description": "The text content to write to the file. Existing file content will be completely replaced. Unicode and special characters are supported with automatic encoding handling."
                }
            },
            "required": ["base_dir", "filename", "content"]
        }
    
    async def run(self, base_dir: str, filename: str, content: str):
        from libs.fileops.file import FileService
        
        service = FileService(base_dir)
        try:
            service.write_to_file(filename, content)
            return {
                "success": True,
                "result": f"Successfully wrote content to {filename} in {base_dir}",
                "filename": filename,
                "base_dir": base_dir
            }
        except Exception as e:
            return {
                "success": False,
                "result": f"Failed to write to file: {str(e)}",
                "filename": filename,
                "base_dir": base_dir
            }