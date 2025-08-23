#!/usr/bin/env python3
"""
Script to convert existing chapter files to use the problemstatement environment
for proper version control support.
"""

import os
import re
import glob
from pathlib import Path

def convert_chapter_file(file_path):
    """Convert a chapter file to use problemstatement environment"""
    print(f"Converting {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match problembox environments that don't already have problemstatement
    # This matches: \begin{problembox}[...] followed by content that's not \begin{problemstatement}
    pattern = r'\\begin\{problembox\}\[([^\]]+)\]\s*\n(?!\s*\\begin\{problemstatement\})(.*?)\\end\{problembox\}'
    
    def replace_problembox(match):
        title = match.group(1)
        content = match.group(2).strip()
        
        # Skip if already has problemstatement
        if '\\begin{problemstatement}' in content:
            return match.group(0)
        
        # Convert to use problemstatement
        return f'\\begin{{problembox}}[{title}]\n\\begin{{problemstatement}}\n{content}\n\\end{{problemstatement}}\n\\end{{problembox}}'
    
    # Apply the conversion
    new_content = re.sub(pattern, replace_problembox, content, flags=re.DOTALL)
    
    # Check if any changes were made
    if new_content != content:
        # Create backup
        backup_path = file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Created backup: {backup_path}")
        
        # Write converted content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✓ Converted successfully")
        return True
    else:
        print(f"  No changes needed (already uses problemstatement or no problembox found)")
        return False

def main():
    print("Converting Chapter Files to Use problemstatement Environment")
    print("=" * 60)
    
    # Find all chapter files
    chapter_files = glob.glob("ch*.tex")
    
    if not chapter_files:
        print("No chapter files (ch*.tex) found in current directory.")
        return
    
    print(f"Found {len(chapter_files)} chapter files:")
    for f in sorted(chapter_files):
        print(f"  - {f}")
    
    print("\nStarting conversion...")
    converted_count = 0
    
    for chapter_file in sorted(chapter_files):
        if convert_chapter_file(chapter_file):
            converted_count += 1
        print()
    
    print("=" * 60)
    print(f"Conversion complete!")
    print(f"Converted {converted_count} out of {len(chapter_files)} files")
    
    if converted_count > 0:
        print("\nNext steps:")
        print("1. Review the converted files to ensure they look correct")
        print("2. Test compilation with both \showproblemstrue and \showproblemsfalse")
        print("3. Delete .backup files once you're satisfied with the results")
    else:
        print("\nNo files needed conversion. Your chapter files are already compatible!")

if __name__ == "__main__":
    main()

