#!/usr/bin/env python3
"""
Standalone test script to demonstrate the new media type folder structure.
Tests the logic without requiring Azure dependencies.
"""

def get_media_type_folder(filename: str, content_type: str = None) -> str:
    """
    Determine the appropriate folder based on file type.
    
    Returns folder name based on media type.
    """
    # Configuration (matches your settings)
    config = {
        'images_folder': 'images',
        'videos_folder': 'videos', 
        'audio_folder': 'audio',
        'documents_folder': 'documents',
        'other_folder': 'other'
    }
    
    # Get file extension
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Check content type first, then fall back to file extension
    if content_type:
        content_type = content_type.lower()
        
        # Image types
        if content_type.startswith('image/'):
            return config['images_folder']
        
        # Video types
        elif content_type.startswith('video/'):
            return config['videos_folder']
        
        # Audio types
        elif content_type.startswith('audio/'):
            return config['audio_folder']
        
        # Document types
        elif content_type in ['application/pdf', 'application/msword', 
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            'application/vnd.ms-excel',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            'application/vnd.ms-powerpoint',
                            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                            'text/plain', 'text/csv']:
            return config['documents_folder']
    
    # Fall back to file extension detection
    # Image extensions
    if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif']:
        return config['images_folder']
    
    # Video extensions
    elif file_ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp', 'mpg', 'mpeg']:
        return config['videos_folder']
    
    # Audio extensions
    elif file_ext in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus']:
        return config['audio_folder']
    
    # Document extensions
    elif file_ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'rtf']:
        return config['documents_folder']
    
    # Default to other folder for unknown types
    else:
        return config['other_folder']


def generate_blob_path(filename: str, content_type: str = None) -> str:
    """
    Generate media-type organized blob path for Discord media.
    
    Pattern: {media_type_folder}/{timestamp}_{filename}
    """
    from datetime import datetime
    import re
    
    # Sanitize filename
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in ".-_":
            safe_chars.append(char)
        else:
            safe_chars.append("_")
    safe_filename = "".join(safe_chars)
    
    # Generate timestamp prefix to avoid conflicts
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    timestamped_filename = f"{timestamp}_{safe_filename}"
    
    # Determine media type folder based on content type and filename
    media_folder = get_media_type_folder(filename, content_type)
    
    return f"{media_folder}/{timestamped_filename}"


def test_media_type_detection():
    """Test the media type folder detection logic."""
    
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
    print("=" * 60)
    
    all_passed = True
    for filename, content_type, expected_folder in test_cases:
        actual_folder = get_media_type_folder(filename, content_type)
        
        status = "✅" if actual_folder == expected_folder else "❌"
        print(f"{status} {filename:<20} ({content_type or 'None':<45}) -> {actual_folder}")
        
        if actual_folder != expected_folder:
            print(f"    Expected: {expected_folder}, Got: {actual_folder}")
            all_passed = False
    
    print("\n🗂️ Expected Folder Structure in Azure Storage:")
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
    
    print("\n📋 Sample Full Blob Paths:")
    sample_files = [
        ("discord_screenshot.png", "image/png"),
        ("funny_video.mp4", "video/mp4"),
        ("voice_note.mp3", "audio/mpeg"),
        ("meeting_notes.pdf", "application/pdf")
    ]
    
    for filename, content_type in sample_files:
        blob_path = generate_blob_path(filename, content_type)
        print(f"  {filename} -> {blob_path}")
    
    print(f"\n🎯 Test Results: {'All tests passed!' if all_passed else 'Some tests failed!'}")
    return all_passed


if __name__ == "__main__":
    test_media_type_detection()
