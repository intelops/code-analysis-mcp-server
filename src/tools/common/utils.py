"""Common utilities for all tool implementations."""

import os
import tempfile
import shutil
from typing import Optional, Dict, Any, List

def create_temp_file(content: str, suffix: str = None) -> str:
    """
    Create a temporary file with the given content.
    
    Args:
        content: The content to write to the file
        suffix: Optional file suffix (e.g., '.py', '.js')
        
    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        return tmp.name

def get_language_extension(language: str) -> str:
    """
    Get the file extension for a given language.
    
    Args:
        language: The language identifier
        
    Returns:
        The file extension (with dot)
    """
    extension_map = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "java": ".java",
        "c": ".c",
        "cpp": ".cpp",
        "csharp": ".cs",
        "go": ".go",
        "ruby": ".rb",
        "php": ".php",
        "rust": ".rs"
    }
    
    return extension_map.get(language, ".txt")

def create_backup(file_path: str) -> str:
    """
    Create a backup of a file.
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        Path to the backup file
    """
    backup_path = f"{file_path}.bak"
    shutil.copy2(file_path, backup_path)
    return backup_path

def is_path_safe(path: str, base_dir: str) -> bool:
    """
    Check if a path is safe (within the base directory).
    
    Args:
        path: The path to check
        base_dir: The base directory
        
    Returns:
        True if the path is safe, False otherwise
    """
    abs_path = os.path.abspath(path)
    abs_base = os.path.abspath(base_dir)
    return abs_path.startswith(abs_base)
