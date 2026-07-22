#!/usr/bin/env python3
"""Fix remaining markdown issues:
1. MD012: Remove multiple consecutive blank lines
2. MD026: Fix trailing punctuation in headings
3. MD040: Add missing language specs
4. MD036: Convert bold text to headings
5. MD060: Fix table spacing
6. MD009: Remove trailing spaces
"""
import re
from pathlib import Path

def fix_multiple_blanks(content):
    """Fix MD012: Multiple consecutive blank lines -> single blank"""
    # Replace 3+ consecutive newlines with 2 newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content

def fix_trailing_punctuation_in_headings(content):
    """Fix MD026: Remove trailing colons from headings"""
    # Fix headings ending with colons
    content = re.sub(r'(#+\s+[^:]+):(\n)', r'\1\2', content)
    return content

def fix_code_block_language(content):
    """Fix MD040: Add language to code blocks"""
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for code fence without language
        if line.strip() == '```':
            # Add language spec
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip() and not next_line.startswith('```'):
                    # Guess language
                    if next_line.strip().startswith(('def ', 'import ', 'from ', 'class ', 'if __name__')):
                        new_lines.append('```python')
                    elif next_line.strip().startswith(('python', 'pip', 'npm')):
                        new_lines.append('```powershell')
                    else:
                        new_lines.append('```text')
                else:
                    new_lines.append('```text')
            else:
                new_lines.append('```text')
        else:
            new_lines.append(line)
        i += 1
    
    return '\n'.join(new_lines)

def fix_bold_as_heading(content):
    """Fix MD036: Convert bold text followed by newline to heading"""
    # Pattern: **Text** at start of line, followed by newline
    # But be careful not to convert bold text within paragraphs
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        # Check if line is just **text** with nothing else
        if re.match(r'^\*\*[^*]+\*\*$', line):
            # Convert to heading
            text = line.replace('**', '').strip()
            # Check if next line is blank - then it's probably meant to be a heading
            if i + 1 < len(lines) and lines[i + 1].strip() == '':
                new_lines.append(f'### {text}')
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def fix_table_spacing(content):
    """Fix MD060: Add proper spacing in table separators"""
    # Fix table separator rows to have proper spacing
    content = re.sub(r'\|\-\-\-', r'| ---', content)
    content = re.sub(r'\-\-\-\|', r'--- |', content)
    return content

def fix_trailing_spaces(content):
    """Fix MD009: Remove trailing spaces"""
    lines = content.split('\n')
    new_lines = [line.rstrip() for line in lines]
    return '\n'.join(new_lines)

def fix_markdown_file(filepath):
    """Apply all fixes to a markdown file."""
    print(f"Processing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Apply all fixes in order
    content = fix_trailing_spaces(content)
    content = fix_multiple_blanks(content)
    content = fix_trailing_punctuation_in_headings(content)
    content = fix_code_block_language(content)
    content = fix_bold_as_heading(content)
    content = fix_table_spacing(content)
    
    # Write back if changed
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Fixed")
        return True
    else:
        print(f"  No changes needed")
        return False

# Fix all markdown files
md_files = [
    'README.md',
    'QUICK_REFERENCE.md',
    'PROFESSIONAL_EDIT_UPGRADES.md',
    'POLISH_RESULTS.md',
    'LEARNING_SYSTEM.md',
    'INTEGRATION_FIXES.md',
    'IMPLEMENTATION_GUIDE.md',
    'FIXES_SUMMARY.md',
    '2026_LEARNING_SYSTEM_LAUNCH.md'
]

workspace = Path('c:\\edit factory')
fixed_count = 0

for md_file in md_files:
    filepath = workspace / md_file
    if filepath.exists():
        if fix_markdown_file(filepath):
            fixed_count += 1
    else:
        print(f"Not found: {md_file}")

print(f"\n✅ Total files fixed: {fixed_count}/{len(md_files)}")
