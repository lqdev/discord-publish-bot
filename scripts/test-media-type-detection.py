#!/usr/bin/env python3
"""
Test script to demonstrate the new media type folder structure for Azure Storage.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from discord_publish_bot.config.settings import AppSettings
from discord_publish_bot.storage.azure_storage import AzureStorageService


def test_media_type_detection():
    """Test the media type folder detection logic."""
    
    # Create test settings
    settings = AppSettings(
        azure_storage={
            'account_name': 'test_account',
            'container_name': 'discord-media',
            'images_folder': 'images',
            'videos_folder': 'videos', 
            'audio_folder': 'audio',
            'documents_folder': 'documents',
            'other_folder': 'other',
            'enabled': True
        },
        discord={'bot_token': 'test', 'application_id': '123', 'public_key': 'test', 'authorized_user_id': '456'},
        github={'token': 'test', 'repository': 'test/test'},
        api={'key': 'test_key_1234567890'}
    )
    
    # Create storage service (won't actually connect without real credentials)
    try:
        storage_service = AzureStorageService(settings)
    except Exception as e:
        print(f"Note: Storage service initialization failed (expected without real Azure credentials): {e}")
        print("Continuing with direct method testing...\n")
        storage_service = None
    
    # Test cases for different file types
    test_cases = [
        # Images
        ("photo.jpg", "image/jpeg", "images"),
        ("screenshot.png", "image/png", "images"),
        ("avatar.gif", "image/gif", "images"),
        ("profile.webp", None, "images"),  # Test extension fallback
        
        # Videos
        ("video.mp4", "video/mp4", "videos"),
        ("clip.avi", "video/x-msvideo", "videos"),
        ("movie.mov", None, "videos"),  # Test extension fallback
        ("stream.webm", "video/webm", "videos"),
        
        # Audio
        ("song.mp3", "audio/mpeg", "audio"),
        ("sound.wav", "audio/wav", "audio"),
        ("music.flac", None, "audio"),  # Test extension fallback
        ("voice.ogg", "audio/ogg", "audio"),
        
        # Documents
        ("document.pdf", "application/pdf", "documents"),
        ("report.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "documents"),
        ("data.xlsx", None, "documents"),  # Test extension fallback
        ("notes.txt", "text/plain", "documents"),
        
        # Other/Unknown
        ("unknown.xyz", "application/octet-stream", "other"),
        ("binary", None, "other"),
        ("no_extension", "unknown/type", "other"),
    ]
    
    print("🧪 Testing Media Type Folder Detection")
    print("=" * 50)
    
    for filename, content_type, expected_folder in test_cases:
        if storage_service:
            # Test with actual service
            actual_folder = storage_service._get_media_type_folder(filename, content_type)
        else:
            # Mock the method for testing
            actual_folder = mock_get_media_type_folder(filename, content_type, settings)
        
        status = "✅" if actual_folder == expected_folder else "❌"
        print(f"{status} {filename:<20} ({content_type or 'None':<40}) -> {actual_folder}")
        
        if actual_folder != expected_folder:
            print(f"    Expected: {expected_folder}, Got: {actual_folder}")
    
    print("\n🗂️ Expected Folder Structure:")
    print("discord-media/")
    print("├── images/")
    print("│   ├── 20250812_143052_photo.jpg")
    print("│   ├── 20250812_143055_screenshot.png")
    print("│   └── 20250812_143058_avatar.gif")
    print("├── videos/")
    print("│   ├── 20250812_143100_video.mp4")
    print("│   └── 20250812_143102_clip.avi")
    print("├── audio/")
    print("│   ├── 20250812_143105_song.mp3")
    print("│   └── 20250812_143107_sound.wav")
    print("├── documents/")
    print("│   ├── 20250812_143110_document.pdf")
    print("│   └── 20250812_143112_report.docx")
    print("└── other/")
    print("    └── 20250812_143115_unknown.xyz")


def mock_get_media_type_folder(filename: str, content_type: str, settings: AppSettings) -> str:
    """
    Mock version of the media type detection for testing without Azure connection.
    """
    storage_config = settings.azure_storage
    
    # Get file extension
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Check content type first, then fall back to file extension
    if content_type:
        content_type = content_type.lower()
        
        # Image types
        if content_type.startswith('image/'):
            return storage_config.images_folder
        
        # Video types
        elif content_type.startswith('video/'):
            return storage_config.videos_folder
        
        # Audio types
        elif content_type.startswith('audio/'):
            return storage_config.audio_folder
        
        # Document types
        elif content_type in ['application/pdf', 'application/msword', 
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            'application/vnd.ms-excel',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            'application/vnd.ms-powerpoint',
                            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                            'text/plain', 'text/csv']:
            return storage_config.documents_folder
    
    # Fall back to file extension detection
    # Image extensions
    if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif']:
        return storage_config.images_folder
    
    # Video extensions
    elif file_ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp', 'mpg', 'mpeg']:
        return storage_config.videos_folder
    
    # Audio extensions
    elif file_ext in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus']:
        return storage_config.audio_folder
    
    # Document extensions
    elif file_ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'rtf']:
        return storage_config.documents_folder
    
    # Default to other folder for unknown types
    else:
        return storage_config.other_folder


if __name__ == "__main__":
    test_media_type_detection()
