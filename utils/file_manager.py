"""
File Manager Utility
Handles file operations for StudyFlow
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict


class FileManager:
    """Utility class for managing files in UserData directory"""
    
    def __init__(self):
        """Initialize file manager"""
        self.base_dir = Path(__file__).parent.parent / "UserData" / "Files"
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_subject_dir(self, subject_id: int) -> Path:
        """Get or create directory for a subject"""
        subject_dir = self.base_dir / str(subject_id)
        subject_dir.mkdir(exist_ok=True)
        return subject_dir
    
    def save_file(self, subject_id: int, source_path: str, file_name: str) -> str:
        """Save a file to the subject directory"""
        subject_dir = self.get_subject_dir(subject_id)
        dest_path = subject_dir / file_name
        
        # Copy file to subject directory
        shutil.copy2(source_path, dest_path)
        
        return str(dest_path)
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from the file system"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
        return False
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    def get_file_size_formatted(self, file_path: str) -> str:
        """Get file size in human-readable format"""
        size = self.get_file_size(file_path)
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} TB"
    
    def open_file(self, file_path: str) -> bool:
        """Open a file with the default system application (cross-platform)"""
        try:
            import platform
            import subprocess
            
            system = platform.system()
            
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            elif system == "Linux":
                subprocess.run(["xdg-open", file_path])
            else:
                # Fallback for other systems
                subprocess.run(["xdg-open", file_path])
            
            return True
        except Exception as e:
            print(f"Error opening file: {e}")
            return False
    
    def rename_file(self, file_path: str, new_name: str) -> bool:
        """Rename a file"""
        try:
            path = Path(file_path)
            new_path = path.parent / new_name
            path.rename(new_path)
            return True
        except Exception as e:
            print(f"Error renaming file: {e}")
            return False

    def get_file_type_icon(self, file_name: str) -> str:
        """Return an icon for a file based on its extension."""
        if not file_name:
            return "📄"

        extension = Path(file_name).suffix.lower()
        icon_map = {
            '.pdf': '📄',
            '.doc': '📝',
            '.docx': '📝',
            '.ppt': '📊',
            '.pptx': '📊',
            '.txt': '📃',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.png': '🖼️',
            '.gif': '🖼️',
            '.zip': '🗜️',
            '.py': '🐍',
            '.cpp': '⚙️',
            '.c': '⚙️',
            '.java': '☕',
            '.mp4': '🎥',
            '.mp3': '🎵',
        }
        return icon_map.get(extension, '📁')

    def sort_files(self, files: List[Dict], sort_by: str = 'name') -> List[Dict]:
        """Sort a list of file records by a supported field."""
        if not files:
            return []

        if sort_by == 'type':
            return sorted(files, key=lambda item: str(item.get('file_type', '')).lower())

        if sort_by == 'size':
            return sorted(files, key=lambda item: str(item.get('file_size', '0 B')).lower())

        return sorted(files, key=lambda item: str(item.get('file_name', '')).lower())


# Global file manager instance
file_manager = FileManager()
