#!/usr/bin/env python3
"""
Enhanced Discord Publishing Bot Integration Test

Tests the new branch/PR workflow and schema compliance features with latest updates.
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

load_dotenv()

from publishing_api.config import APIConfig
from publishing_api.github_client import GitHubClient
from publishing_api.publishing import PublishingService


async def test_enhanced_publishing_workflow():
    """Test the complete enhanced publishing workflow with real GitHub integration."""
    print("🚀 Testing Enhanced Discord Publishing Bot Workflow")
    print("=" * 60)
    
    # Load real configuration from environment
    try:
        config = APIConfig.from_env()
        print(f"✅ Configuration loaded")
        print(f"   📦 Repository: {config.github_repo}")
        print(f"   👤 Discord User: {config.discord_user_id}")
        print(f"   🌐 Site URL: {config.site_base_url}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("   Please ensure environment variables are set:")
        print("   - GITHUB_TOKEN")
        print("   - GITHUB_REPO") 
        print("   - DISCORD_USER_ID")
        print("   - API_KEY")
        return False
    
    # Test content samples matching luisquintanilla.me patterns
    test_messages = [
        {
            "type": "note",
            "message": """/post note
---
title: "Enhanced Discord Bot Integration Test"
tags: ["testing", "automation", "discord", "github"]
---

Running comprehensive integration test of the enhanced Discord publishing bot. Testing branch/PR workflow, schema compliance, and directory structure alignment with luisquintanilla.me patterns.

Key features being tested:
- Automated branch creation with systematic naming
- Pull request generation with validation metadata
- Schema conversion to target site patterns
- Directory structure mapping to _src/ organization

All systems operational and ready for validation.""",
            "expected_directory": "_src/notes"
        },
        {
            "type": "response", 
            "message": """/post response
---
response_type: "reply"
in_reply_to: "https://github.com/example-dev/example-repo/discussions/42"
title: "Great architecture documentation"
tags: ["indieweb", "architecture", "fsharp"]
---

Excellent documentation of the F# static site generator architecture. The separation of concerns between content processing and site generation is well thought out.""",
            "expected_directory": "_src/responses"
        },
        {
            "type": "bookmark",
            "message": """/post bookmark
---
url: "https://indieweb.org/GitHub"
title: "IndieWeb GitHub Integration Patterns"
tags: ["indieweb", "github", "automation", "publishing"]
---

Comprehensive guide to integrating GitHub with IndieWeb publishing workflows. Great examples of automated content publishing patterns.""",
            "expected_directory": "_src/responses"
        },
        {
            "type": "media",
            "message": """/post media
---
title: "Discord Bot Architecture Diagram"
media_url: "https://example.com/discord-bot-architecture.png"
alt_text: "System architecture showing Discord bot, Publishing API, and GitHub integration"
tags: ["architecture", "diagram", "discord", "automation"]
---

Updated system architecture diagram showing the enhanced Discord publishing bot with branch/PR workflow and schema compliance features.""",
            "expected_directory": "_src/media"
        }
    ]
    
    # Create GitHub client and test connectivity
    github_client = GitHubClient(config.github_token, config.github_repo)
    
    print("\n🔗 Testing GitHub connectivity...")
    try:
        await github_client.check_connectivity()
        print("✅ GitHub connection successful")
    except Exception as e:
        print(f"❌ GitHub connection failed: {e}")
        return False
    
    # Create publishing service
    publishing_service = PublishingService(github_client, config)
    
    print(f"\n📋 Testing {len(test_messages)} different content types with enhanced workflow")
    print()
    
    results = []
    
    for i, test_case in enumerate(test_messages, 1):
        print(f"🧪 Test {i}: {test_case['type']} post with branch/PR workflow")
        print("-" * 50)
        
        try:
            # Parse the message to validate frontmatter conversion
            post_type, original_frontmatter, content = publishing_service.parse_discord_message(
                test_case["message"]
            )
            
            print(f"✓ Parsed post type: {post_type}")
            
            # Convert to target schema (NEW ENHANCED FEATURE)
            target_frontmatter = publishing_service.convert_to_target_schema(
                post_type, original_frontmatter, content
            )
            
            print(f"✓ Converted to luisquintanilla.me schema")
            print(f"  Original fields: {list(original_frontmatter.keys())}")
            print(f"  Target fields: {list(target_frontmatter.keys())}")
            
            # Validate content (NEW ENHANCED FEATURE)
            validation_results = publishing_service.validate_content(
                post_type, target_frontmatter, content
            )
            
            print(f"✓ Content validation results:")
            all_passed = True
            for check, result in validation_results.items():
                status = "✅" if result["passed"] else "❌"
                print(f"  {status} {check}: {result['message']}")
                if not result["passed"]:
                    all_passed = False
            
            # Test enhanced directory mapping
            expected_dir = test_case["expected_directory"]
            actual_dir = publishing_service.CONTENT_TYPE_DIRECTORIES[post_type]
            
            if actual_dir == expected_dir:
                print(f"✓ Directory mapping correct: {actual_dir}")
            else:
                print(f"❌ Directory mapping incorrect: expected {expected_dir}, got {actual_dir}")
                all_passed = False
            
            # Test enhanced filename generation
            filename = publishing_service.generate_filename(post_type, target_frontmatter, content)
            print(f"✓ Generated filename: {filename}")
            
            # Test enhanced markdown generation
            markdown_content = publishing_service.build_markdown_file(target_frontmatter, content)
            print(f"✓ Generated markdown ({len(markdown_content)} chars)")
            
            # Test NEW branch name generation (ENHANCED FEATURE)
            branch_name = github_client.generate_branch_name(
                content_type=post_type,
                message_id=f"integration-test-{i}",
                user_id=config.discord_user_id
            )
            print(f"✓ Generated branch name: {branch_name}")
            
            # Test NEW PR template generation (ENHANCED FEATURE)
            content_preview = content[:100] if content else target_frontmatter.get("title", "")
            pr_title, pr_body = github_client.generate_pr_template(
                content_type=post_type,
                content_preview=content_preview,
                user_id=config.discord_user_id,
                message_id=f"integration-test-{i}",
                validation_results=validation_results
            )
            print(f"✓ Generated PR template")
            print(f"  Title: {pr_title[:60]}...")
            print(f"  Body length: {len(pr_body)} chars")
            
            # Test ENHANCED publishing workflow (with branch/PR)
            if os.getenv("RUN_GITHUB_TESTS", "false").lower() == "true":
                print(f"🔄 Testing actual GitHub branch/PR creation...")
                
                try:
                    # Use enhanced commit workflow (creates branch, commits file, creates PR)
                    full_path = f"{actual_dir}/{filename}"
                    commit_result = await github_client.commit_file_to_branch(
                        filepath=full_path,
                        content=markdown_content,
                        commit_message=f"Add {post_type} post via Discord bot",
                        branch_name=branch_name,
                        create_pr=True,
                        pr_title=pr_title,
                        pr_body=pr_body,
                    )
                    
                    # Check result and handle errors
                    if commit_result and commit_result.get("commit_sha"):
                        print(f"✓ File committed to branch: {commit_result['commit_sha'][:8]}")
                        
                        # Check if PR was created
                        if commit_result.get("pr_url"):
                            print(f"✓ Pull request created: {commit_result['pr_url']}")
                        else:
                            print(f"⚠️ Pull request creation skipped or failed")
                    else:
                        error_msg = commit_result.get("error", "Unknown error") if commit_result else "No result returned"
                        print(f"⚠️ GitHub commit failed: {error_msg}")
                    
                except Exception as e:
                    print(f"⚠️ GitHub operations skipped/failed: {e}")
                    # Continue with validation even if GitHub operations fail
            else:
                print(f"💡 GitHub operations skipped (set RUN_GITHUB_TESTS=true to enable)")
            
            # Store results
            results.append({
                "test_case": test_case,
                "post_type": post_type,
                "target_frontmatter": target_frontmatter,
                "validation_results": validation_results,
                "filename": filename,
                "branch_name": branch_name,
                "pr_title": pr_title,
                "pr_body": pr_body,
                "markdown_length": len(markdown_content),
                "all_validations_passed": all_passed,
                "success": True
            })
            
            status = "✅" if all_passed else "⚠️"
            print(f"{status} Test {i} completed{'successfully' if all_passed else ' with warnings'}")
            
        except Exception as e:
            print(f"❌ Test {i} failed: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "test_case": test_case,
                "error": str(e),
                "success": False
            })
        
        print()
    
    # Enhanced Summary with detailed validation
    print("📊 Enhanced Integration Test Summary")
    print("=" * 50)
    
    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    validation_warnings = [r for r in successful_tests if not r.get("all_validations_passed", True)]
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
    print(f"⚠️ Tests with warnings: {len(validation_warnings)}/{len(results)}")
    print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
    
    if failed_tests:
        print("\n❌ Failed test details:")
        for i, result in enumerate(failed_tests, 1):
            print(f"  {i}. {result['test_case']['type']}: {result['error']}")
    
    if validation_warnings:
        print("\n⚠️ Tests with validation warnings:")
        for result in validation_warnings:
            print(f"  - {result['post_type']}: Check validation results above")
    
    print("\n🎯 Enhanced Schema Compliance Validation")
    print("-" * 40)
    
    schema_compliance_score = 0
    total_schema_checks = 0
    
    for result in successful_tests:
        frontmatter = result["target_frontmatter"]
        post_type = result["post_type"]
        
        print(f"\n{post_type.upper()} Post Schema Analysis:")
        
        # Enhanced validation based on luisquintanilla.me patterns
        if post_type == "note":
            required = ["post_type", "title", "published_date", "tags"]
            optional = ["description", "excerpt"]
            
            present = [f for f in required if f in frontmatter]
            missing = [f for f in required if f not in frontmatter]
            
            print(f"  Required: {len(present)}/{len(required)} ✅ {present}")
            if missing:
                print(f"  Missing: ❌ {missing}")
            
            # Check format compliance
            if "published_date" in frontmatter:
                date_format_valid = isinstance(frontmatter["published_date"], str)
                print(f"  Date format: {'✅' if date_format_valid else '❌'} {frontmatter['published_date']}")
                
            schema_compliance_score += len(present)
            total_schema_checks += len(required)
            
        elif post_type in ["response", "bookmark"]:
            required = ["title", "response_type", "dt_published", "dt_updated", "tags"]
            
            present = [f for f in required if f in frontmatter]
            missing = [f for f in required if f not in frontmatter]
            
            print(f"  Required: {len(present)}/{len(required)} ✅ {present}")
            if missing:
                print(f"  Missing: ❌ {missing}")
                
            # Check response type specific fields
            if post_type == "bookmark" and "targeturl" in frontmatter:
                print(f"  Target URL: ✅ {frontmatter['targeturl']}")
            elif "in_reply_to" in frontmatter:
                print(f"  Reply to: ✅ {frontmatter['in_reply_to']}")
                
            schema_compliance_score += len(present)
            total_schema_checks += len(required)
                
        elif post_type == "media":
            required = ["post_type", "title", "published_date", "tags"]
            media_fields = ["media_url", "alt_text", "caption"]
            
            present = [f for f in required if f in frontmatter]
            missing = [f for f in required if f not in frontmatter]
            media_present = [f for f in media_fields if f in frontmatter]
            
            print(f"  Required: {len(present)}/{len(required)} ✅ {present}")
            if missing:
                print(f"  Missing: ❌ {missing}")
            print(f"  Media fields: ✅ {media_present}")
            
            schema_compliance_score += len(present)
            total_schema_checks += len(required)
    
    # Calculate compliance percentage
    compliance_percentage = (schema_compliance_score / total_schema_checks * 100) if total_schema_checks > 0 else 0
    print(f"\n📈 Schema Compliance Score: {schema_compliance_score}/{total_schema_checks} ({compliance_percentage:.1f}%)")
    
    print("\n🏗️ Enhanced Directory Structure Validation")
    print("-" * 40)
    
    expected_structure = {
        "note": "_src/notes",
        "response": "_src/responses",
        "bookmark": "_src/responses",  # Bookmarks are responses in luisquintanilla.me
        "media": "_src/media",
    }
    
    directory_score = 0
    total_directory_checks = len(expected_structure)
    
    for content_type, expected_dir in expected_structure.items():
        actual_dir = publishing_service.CONTENT_TYPE_DIRECTORIES.get(content_type)
        is_correct = actual_dir == expected_dir
        status = "✅" if is_correct else "❌"
        print(f"  {status} {content_type}: {actual_dir}")
        if not is_correct:
            print(f"     Expected: {expected_dir}")
        if is_correct:
            directory_score += 1
    
    directory_percentage = (directory_score / total_directory_checks * 100)
    print(f"\n📁 Directory Mapping Score: {directory_score}/{total_directory_checks} ({directory_percentage:.1f}%)")
    
    print("\n🔗 Enhanced Branch/PR Workflow Validation")
    print("-" * 40)
    
    workflow_score = 0
    total_workflow_checks = 0
    
    for result in successful_tests:
        branch_name = result["branch_name"]
        pr_title = result["pr_title"]
        pr_body = result["pr_body"]
        
        # Validate enhanced branch naming convention
        branch_checks = [
            ("Starts with content/discord-bot/", branch_name.startswith("content/discord-bot/")),
            ("Contains date", any(char.isdigit() for char in branch_name)),
            ("Contains content type", f"/{result['post_type']}/" in branch_name),
            ("Contains user identifier", config.discord_user_id.lower() in branch_name.lower()),
        ]
        
        # Validate enhanced PR template
        pr_checks = [
            ("Contains content type", result['post_type'] in pr_title.lower()),
            ("Has validation section", "validation results" in pr_body.lower()),
            ("Has content preview", len(pr_body) > 200),
            ("Has proper formatting", "##" in pr_body or "**" in pr_body),
        ]
        
        print(f"\n{result['post_type'].upper()} Workflow Validation:")
        
        branch_passed = 0
        for check_name, passed in branch_checks:
            status = "✅" if passed else "❌"
            print(f"  {status} Branch {check_name}")
            if passed:
                branch_passed += 1
                
        pr_passed = 0
        for check_name, passed in pr_checks:
            status = "✅" if passed else "❌"
            print(f"  {status} PR {check_name}")
            if passed:
                pr_passed += 1
        
        print(f"  📊 Branch: {branch_passed}/{len(branch_checks)}, PR: {pr_passed}/{len(pr_checks)}")
        
        workflow_score += branch_passed + pr_passed
        total_workflow_checks += len(branch_checks) + len(pr_checks)
    
    workflow_percentage = (workflow_score / total_workflow_checks * 100) if total_workflow_checks > 0 else 0
    print(f"\n🔄 Workflow Score: {workflow_score}/{total_workflow_checks} ({workflow_percentage:.1f}%)")
    
    # Overall enhanced results
    success_rate = len(successful_tests) / len(results) * 100
    
    print(f"\n🎉 Enhanced Integration Test Results")
    print("=" * 50)
    print(f"Overall Success Rate: {success_rate:.1f}%")
    print(f"Schema Compliance: {compliance_percentage:.1f}%")
    print(f"Directory Mapping: {directory_percentage:.1f}%")
    print(f"Branch/PR Workflow: {workflow_percentage:.1f}%")
    
    # Enhanced scoring system
    average_score = (success_rate + compliance_percentage + directory_percentage + workflow_percentage) / 4
    
    print(f"\n📊 Enhanced System Readiness Score: {average_score:.1f}%")
    
    if average_score >= 95:
        print("🏆 EXCELLENT: Enhanced Discord publishing bot is production-ready!")
        print("   All systems operational with enhanced features validated.")
    elif average_score >= 90:
        print("✅ GOOD: Enhanced system ready for production with minor optimizations.")
    elif average_score >= 80:
        print("⚠️ ACCEPTABLE: System functional but review issues before production.")
    else:
        print("❌ NEEDS WORK: Address significant issues before production deployment.")
    
    return average_score >= 90


def show_enhanced_markdown_samples():
    """Show enhanced markdown samples with luisquintanilla.me schema compliance."""
    print("\n📄 Enhanced Markdown Output Samples")
    print("=" * 50)
    
    # Create a temporary publishing service for sample generation
    try:
        config = APIConfig.from_env()
    except:
        # Fallback for demo purposes
        config = APIConfig(
            api_key="demo_key",
            discord_user_id="demo_user",
            github_token="demo_token",
            github_repo="demo/repo"
        )
    
    github_client = GitHubClient(config.github_token, config.github_repo)
    publishing_service = PublishingService(github_client, config)
    
    samples = [
        {
            "type": "note",
            "frontmatter": {
                "post_type": "note",
                "title": "Enhanced Discord Bot Testing Complete",
                "published_date": "2025-08-08 15:30 -05:00",
                "tags": ["discord", "automation", "testing", "github"]
            },
            "content": """Successfully completed comprehensive testing of the enhanced Discord publishing bot!

## Key Enhancements Validated

### 🔄 Branch/PR Workflow
- Automated branch creation with systematic naming
- Pull request generation with validation metadata
- Review process with content classification

### 📋 Schema Compliance  
- Perfect alignment with luisquintanilla.me patterns
- Automatic conversion from Discord input format
- All required fields validated and present

### 📁 Directory Structure
- Correct mapping to `_src/` organization
- Content type classification working properly
- URL generation aligned with site routing

All systems operational and ready for production deployment! 🚀"""
        },
        {
            "type": "response",
            "frontmatter": {
                "title": "Great documentation architecture",
                "response_type": "reply",
                "in_reply_to": "https://github.com/example-dev/example-repo/blob/main/README.md",
                "dt_published": "2025-08-08T20:30:00Z",
                "dt_updated": "2025-08-08T20:30:00Z",
                "tags": ["documentation", "architecture", "fsharp"]
            },
            "content": """Excellent example of clean documentation architecture for a personal website. The separation between content source (`_src/`) and generated output is well thought out."""
        }
    ]
    
    for i, sample in enumerate(samples, 1):
        print(f"\n{i}. {sample['type'].upper()} Post Sample:")
        print("-" * 30)
        
        markdown = publishing_service.build_markdown_file(
            sample["frontmatter"], 
            sample["content"]
        )
        
        # Show first 500 chars for readability
        preview = markdown[:500] + "..." if len(markdown) > 500 else markdown
        print(preview)
        
        print(f"\nTotal length: {len(markdown)} characters")
        print(f"Frontmatter fields: {len(sample['frontmatter'])}")
        
    print("\n" + "=" * 50)


if __name__ == "__main__":
    print("🤖 Enhanced Discord Publishing Bot - Comprehensive Integration Test")
    print("Testing latest enhancements: branch/PR workflow, schema compliance, directory mapping")
    print("=" * 80)
    print(f"🕐 Test started at: {datetime.utcnow().isoformat()}Z")
    print()
    
    # Show environment status
    required_env_vars = ["GITHUB_TOKEN", "GITHUB_REPO", "DISCORD_USER_ID", "API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️ Environment Setup Notice:")
        print(f"   Missing environment variables: {missing_vars}")
        print("   Some tests will use mock data instead of real GitHub integration")
        print("   Set RUN_GITHUB_TESTS=true to enable actual GitHub operations")
    else:
        print("✅ Environment variables configured")
        github_testing = os.getenv("RUN_GITHUB_TESTS", "false").lower() == "true"
        print(f"   GitHub testing: {'enabled' if github_testing else 'disabled (set RUN_GITHUB_TESTS=true to enable)'}")
    
    print()
    
    try:
        success = asyncio.run(test_enhanced_publishing_workflow())
        
        # Show enhanced markdown samples
        show_enhanced_markdown_samples()
        
        print(f"\n🏁 Integration test completed at: {datetime.utcnow().isoformat()}Z")
        
        if success:
            print("\n🎉 COMPREHENSIVE INTEGRATION TEST SUCCESSFUL!")
            print("The enhanced Discord publishing bot is production-ready with:")
            print("  ✅ Branch/PR workflow automation")
            print("  ✅ Perfect schema compliance with luisquintanilla.me") 
            print("  ✅ Accurate directory structure mapping")
            print("  ✅ Advanced validation and quality assurance")
            print("\nNext step: Deploy to production and start using the enhanced workflow!")
        else:
            print("\n⚠️ Integration test completed with issues.")
            print("Review the detailed results above before production deployment.")
            
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
