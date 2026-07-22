#!/usr/bin/env python3
"""Final pass to fix remaining 23 markdown errors"""
import re
from pathlib import Path

def fix_remaining_issues():
    workspace = Path('c:\\edit factory')
    
    # Fix 2026_LEARNING_SYSTEM_LAUNCH.md
    file_path = workspace / '2026_LEARNING_SYSTEM_LAUNCH.md'
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix bold-as-heading patterns - convert **Text** on its own line to #### Text
    # Match lines that are just **text**
    content = re.sub(
        r'^(\*\*[^*]+\*\*)$',
        lambda m: '#### ' + m.group(1)[2:-2],  # Remove ** and add ####
        content,
        flags=re.MULTILINE
    )
    
    # Fix bare ``` blocks with ```text
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == '```':
            # Look ahead
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # If next line is not empty and not another fence
                if next_line and not next_line.startswith('```'):
                    # This block has content, add language
                    new_lines.append('```text')
                else:
                    # Empty or end of block
                    new_lines.append('```text')
            else:
                new_lines.append('```text')
        else:
            new_lines.append(line)
        i += 1
    
    content = '\n'.join(new_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Fixed 2026_LEARNING_SYSTEM_LAUNCH.md")
    
    # Fix FIXES_SUMMARY.md
    file_path = workspace / 'FIXES_SUMMARY.md'
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix bare ``` blocks
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == '```':
            # Add language if not present
            new_lines.append('```text')
        else:
            new_lines.append(line)
        i += 1
    
    content = '\n'.join(new_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Fixed FIXES_SUMMARY.md")

fix_remaining_issues()
print("\n✅ Final fixes applied")
