#!/usr/bin/env python3
"""Aggressively fix all remaining bare code blocks"""
import re
from pathlib import Path

def fix_code_blocks(content):
    """Replace bare ``` with ```text"""
    # Look for ``` that is alone on a line and not followed by a language
    # The key is to look for lines that are JUST ``` characters
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Is this a fence line (only backticks, possibly with leading/trailing space)?
        if stripped and all(c == '`' for c in stripped) and len(stripped) == 3:
            # This is a bare ``` fence
            # Check if we should add language
            # Look ahead to see if there's content or if it's a closing fence
            is_opening = False
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # If next line exists and isn't blank and isn't another fence
                if next_line.strip() and not (next_line.strip() and all(c == '`' for c in next_line.strip())):
                    # Looks like an opening fence with content
                    is_opening = True
            
            if is_opening:
                # Add language
                new_lines.append(line.replace('```', '```text'))
            else:
                # Closing fence or empty block - might also need language
                new_lines.append(line.replace('```', '```text'))
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def fix_bold_heading(content):
    """Replace **Text** on own line with #### Text"""
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Check if line is just **text** pattern
        match = re.match(r'^\*\*([^*]+)\*\*$', stripped)
        if match:
            # Convert to heading
            text = match.group(1)
            # Preserve indentation
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f'{indent}#### {text}')
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

files_to_fix = [
    Path('c:\\edit factory\\2026_LEARNING_SYSTEM_LAUNCH.md'),
    Path('c:\\edit factory\\FIXES_SUMMARY.md'),
]

for file_path in files_to_fix:
    print(f"Processing {file_path.name}...")
    content = file_path.read_text(encoding='utf-8')
    
    # Apply fixes
    content = fix_code_blocks(content)
    content = fix_bold_heading(content)
    
    file_path.write_text(content, encoding='utf-8')
    print(f"  ✓ Fixed {file_path.name}")

print("\n✅ All remaining issues fixed")
