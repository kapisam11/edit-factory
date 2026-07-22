#!/usr/bin/env python3
"""Direct line-by-line fix for remaining bare code blocks"""
from pathlib import Path

files = [
    ('c:\\edit factory\\2026_LEARNING_SYSTEM_LAUNCH.md', [307, 317, 355, 227]),  # Lines with bare ```
    ('c:\\edit factory\\FIXES_SUMMARY.md', [153, 165, 173, 182, 193, 208]),
]

for file_path_str, problem_lines in files:
    file_path = Path(file_path_str)
    lines = file_path.read_text(encoding='utf-8').split('\n')
    
    # Fix bare ``` on specified lines (1-indexed from linter, convert to 0-indexed)
    for line_num in problem_lines:
        idx = line_num - 1  # Convert to 0-indexed
        if idx < len(lines) and lines[idx].strip() == '```':
            lines[idx] = '```text'
            print(f"✓ Fixed line {line_num} in {file_path.name}")
    
    file_path.write_text('\n'.join(lines), encoding='utf-8')

print("\n✅ Fixed all bare code blocks")
