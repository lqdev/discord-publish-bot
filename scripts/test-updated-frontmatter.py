#!/usr/bin/env python3
"""
Test the updated frontmatter format against VS Code metadata snippets.
"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from publishing_api.publishing import PublishingService
from publishing_api.config import APIConfig

def test_frontmatter_formats():
    """Test the updated frontmatter conversion."""
    print("🧪 Testing Updated Frontmatter Format")
    print("=" * 50)
    
    # Create service
    config = APIConfig.from_env()
    service = PublishingService(None, config)
    
    # Test data
    test_cases = [
        {
            "name": "Note Post",
            "post_type": "note",
            "frontmatter": {
                "type": "note",
                "date": "2025-08-08T21:30:00Z",
                "title": "Testing the new frontmatter format",
                "tags": ["test", "frontmatter"]
            },
            "content": "This is a test note to verify the new frontmatter format."
        },
        {
            "name": "Bookmark Post", 
            "post_type": "bookmark",
            "frontmatter": {
                "type": "bookmark",
                "date": "2025-08-08T21:30:00Z",
                "title": "Great Resource on Static Sites",
                "url": "https://example.com/static-sites",
                "tags": ["resources", "static-sites"]
            },
            "content": "Found this excellent resource on building static sites."
        },
        {
            "name": "Media Post",
            "post_type": "media", 
            "frontmatter": {
                "type": "media",
                "date": "2025-08-08T21:30:00Z",
                "title": "System Architecture Diagram",
                "media_url": "https://example.com/diagram.png",
                "alt_text": "System architecture showing API flow",
                "tags": ["architecture", "diagrams"]
            },
            "content": "Updated system architecture diagram."
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        # Convert frontmatter
        converted = service.convert_to_target_schema(
            test_case["post_type"],
            test_case["frontmatter"], 
            test_case["content"]
        )
        
        # Build markdown
        markdown = service.build_markdown_file(converted, test_case["content"])
        
        print("Converted Frontmatter:")
        print(f"  Fields: {list(converted.keys())}")
        for key, value in converted.items():
            print(f"  {key}: {repr(value)}")
        
        print(f"\nGenerated Markdown:")
        print("```markdown")
        print(markdown)
        print("```")
        
        # Check directory mapping
        expected_dir = service.CONTENT_TYPE_DIRECTORIES.get(test_case["post_type"])
        print(f"\nDirectory: {expected_dir}")

if __name__ == "__main__":
    test_frontmatter_formats()
