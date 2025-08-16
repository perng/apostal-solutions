#!/usr/bin/env python3
"""
Script to add \qed at the end of each solution and proof in LaTeX files.
"""

import os
import re
import glob

def add_qed_to_file(filepath):
    """Add \qed at the end of each solution and proof in a LaTeX file."""
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content into lines
    lines = content.split('\n')
    modified = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a solution or proof
        if re.match(r'.*\{Solution:', line) or re.match(r'.*\{Proof:', line):
            # Find where this solution/proof ends
            j = i + 1
            while j < len(lines):
                # Look for the next problembox, section, or chapter
                if (re.match(r'^\s*\\begin\{problembox', lines[j]) or 
                    re.match(r'^\s*\\section\{', lines[j]) or 
                    re.match(r'^\s*\\chapter\{', lines[j]) or
                    re.match(r'^\s*\\subsection\{', lines[j])):
                    break
                j += 1
            
            # Check if the solution/proof already ends with \qed
            if j > i + 1:
                # Look at the last few lines of the solution/proof
                end_lines = lines[i+1:j]
                # Remove empty lines at the end
                while end_lines and end_lines[-1].strip() == '':
                    end_lines.pop()
                
                if end_lines and not end_lines[-1].strip().endswith('\\qed'):
                    # Add \qed before the next problembox/section
                    if j < len(lines):
                        lines.insert(j, '\\qed')
                        lines.insert(j, '')  # Add empty line before \qed
                        modified = True
                        print(f"  Added \\qed at line {j}")
            
            i = j
        else:
            i += 1
    
    if modified:
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"  Modified {filepath}")
    else:
        print(f"  No changes needed for {filepath}")

def main():
    """Main function to process all LaTeX files."""
    # Find all .tex files in the apostol directory
    tex_files = glob.glob('*/ch*.tex')
    
    print(f"Found {len(tex_files)} LaTeX files to process:")
    for file in tex_files:
        print(f"  {file}")
    
    print("\nProcessing files...")
    for filepath in tex_files:
        add_qed_to_file(filepath)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
