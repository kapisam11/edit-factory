#!/usr/bin/env python3
"""Direct string replacements for remaining errors"""
from pathlib import Path

workspace = Path('c:\\edit factory')

# Fix 2026_LEARNING_SYSTEM_LAUNCH.md
file_path = workspace / '2026_LEARNING_SYSTEM_LAUNCH.md'
content = file_path.read_text(encoding='utf-8')

# Replace patterns
replacements = [
    # Line 228 - Test Results code block
    ('## Test Results\n\n```\nPASSED', '## Test Results\n\n```text\nPASSED'),
    
    # Line 268-295 bold-as-heading patterns
    ('\n**Topic Expertise (Per-Topic)**\n', '\n#### Topic Expertise (Per-Topic)\n'),
    ('\n**2026 Video Standards**\n', '\n#### 2026 Video Standards\n'),
    ('\n**Filter Effectiveness**\n', '\n#### Filter Effectiveness\n'),
    ('\n**Request History**\n', '\n#### Request History\n'),
    
    # Line 308, 318, 356 - Cycle code blocks
    ('### Cycle 1: Initial Request\n1. User: "make a COD', '### Cycle 1: Initial Request\n\n```text\n1. User: "make a COD'),
    ('### Cycle 2: Learning & Improvement\n1. User makes second', '### Cycle 2: Learning & Improvement\n\n```text\n1. User makes second'),
    ('### Cycle 3: Perfect Execution\n1. User: "make a', '### Cycle 3: Perfect Execution\n\n```text\n1. User: "make a'),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"✓ Replaced pattern")
    else:
        print(f"⚠ Pattern not found: {old[:50]}")

file_path.write_text(content, encoding='utf-8')
print(f"✓ Saved {file_path.name}")

# Fix FIXES_SUMMARY.md
file_path = workspace / 'FIXES_SUMMARY.md'
content = file_path.read_text(encoding='utf-8')

replacements = [
    ('### Test 1: Core Module Imports\n\n```\nPASS', '### Test 1: Core Module Imports\n\n```text\nPASS'),
    ('### Test 2: Type Annotations\n\n```\nPASS', '### Test 2: Type Annotations\n\n```text\nPASS'),
    ('### Test 3: Integration Pipeline\n\n```\nPASS', '### Test 3: Integration Pipeline\n\n```text\nPASS'),
    ('### Test 4: Filter Effectiveness System\n\n```\nPASS', '### Test 4: Filter Effectiveness System\n\n```text\nPASS'),
    ('### Before (Broken)\n```\n', '### Before (Broken)\n\n```text\n'),
    ('### After (Fixed)\n```\n', '### After (Fixed)\n\n```text\n'),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"✓ Replaced pattern")
    else:
        print(f"⚠ Pattern not found: {old[:50]}")

file_path.write_text(content, encoding='utf-8')
print(f"✓ Saved {file_path.name}")

print("\n✅ Final manual fixes applied")
