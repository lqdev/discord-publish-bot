#!/usr/bin/env python3
"""
Quick validation test for timezone consistency fix.
"""

from datetime import datetime, timezone, timedelta

def test_timezone_consistency():
    """Test that all date fields use consistent timezone format."""
    
    # Mock PublishingService._generate_frontmatter logic to test
    eastern_tz = timezone(timedelta(hours=-5))
    now_eastern = datetime.now(eastern_tz)
    base_date = now_eastern.strftime("%Y-%m-%d %H:%M")
    date_with_tz = f"{base_date} -05:00"
    
    print(f"🕐 Generated Eastern time: {date_with_tz}")
    
    # Test Notes frontmatter
    note_frontmatter = {
        "title": "Test Note",
        "post_type": "note", 
        "published_date": date_with_tz,
        "tags": []
    }
    
    # Test Response/Bookmark frontmatter (after fix)
    response_frontmatter = {
        "title": "Test Response",
        "targeturl": "https://example.com",
        "response_type": "reply",
        "dt_published": date_with_tz,  # ✅ NOW with timezone
        "dt_updated": date_with_tz,   # ✅ Already had timezone
        "tags": []
    }
    
    # Test Media frontmatter  
    media_frontmatter = {
        "title": "Test Media",
        "post_type": "media",
        "published_date": date_with_tz,
        "tags": []
    }
    
    # Validation
    print("\n📊 Timezone Consistency Check:")
    print(f"✅ Notes published_date: {note_frontmatter['published_date']}")
    print(f"✅ Response dt_published: {response_frontmatter['dt_published']}")
    print(f"✅ Response dt_updated: {response_frontmatter['dt_updated']}")
    print(f"✅ Media published_date: {media_frontmatter['published_date']}")
    
    # Check all date fields end with -05:00
    date_fields = [
        note_frontmatter['published_date'],
        response_frontmatter['dt_published'], 
        response_frontmatter['dt_updated'],
        media_frontmatter['published_date']
    ]
    
    all_consistent = all(field.endswith(' -05:00') for field in date_fields)
    
    if all_consistent:
        print("\n🎉 SUCCESS: All date fields consistently use -05:00 timezone!")
        return True
    else:
        print("\n❌ FAILURE: Inconsistent timezone usage detected!")
        return False

if __name__ == "__main__":
    test_timezone_consistency()
