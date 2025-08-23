#!/usr/bin/env python3
"""
Script to build both versions of the Apostol solutions book:
1. With problem statements
2. Solutions only
"""

import os
import subprocess
import shutil
from pathlib import Path

def modify_flag(show_problems=True):
    """Modify the showproblems flag in apostol.tex"""
    tex_file = "apostol.tex"
    
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if show_problems:
        # Set flag to show problems
        content = content.replace(r'\showproblemsfalse', r'\showproblemstrue')
        content = content.replace(r'\showproblemstrue  % Change this to', r'\showproblemstrue  % Change this to')
    else:
        # Set flag to hide problems
        content = content.replace(r'\showproblemstrue', r'\showproblemsfalse')
        content = content.replace(r'\showproblemsfalse  % Change this to', r'\showproblemsfalse  % Change this to')
    
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(content)

def compile_latex():
    """Compile the LaTeX document"""
    try:
        # Run pdflatex twice to ensure proper TOC generation
        subprocess.run(['pdflatex', '-interaction=nonstopmode', 'apostol.tex'], 
                      check=True, capture_output=True)
        subprocess.run(['pdflatex', '-interaction=nonstopmode', 'apostol.tex'], 
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error compiling LaTeX: {e}")
        return False

def main():
    print("Building Apostol Solutions Book - Both Versions")
    print("=" * 50)
    
    # Ensure we're in the right directory
    if not os.path.exists("apostol.tex"):
        print("Error: apostol.tex not found. Please run this script from the apostol directory.")
        return
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Version 1: With problem statements
    print("\n1. Building version WITH problem statements...")
    modify_flag(show_problems=True)
    if compile_latex():
        shutil.copy("apostol.pdf", output_dir / "apostol_with_problems.pdf")
        print("✓ Successfully created apostol_with_problems.pdf")
    else:
        print("✗ Failed to compile version with problems")
    
    # Version 2: Solutions only
    print("\n2. Building version WITHOUT problem statements...")
    modify_flag(show_problems=False)
    if compile_latex():
        shutil.copy("apostol.pdf", output_dir / "apostol_solutions_only.pdf")
        print("✓ Successfully created apostol_solutions_only.pdf")
    else:
        print("✗ Failed to compile solutions-only version")
    
    # Clean up auxiliary files
    print("\n3. Cleaning up auxiliary files...")
    aux_files = ['.aux', '.log', '.toc', '.out', '.fdb_latexmk', '.fls', '.synctex.gz']
    for ext in aux_files:
        if os.path.exists(f"apostol{ext}"):
            os.remove(f"apostol{ext}")
    
    print("\n" + "=" * 50)
    print("Build complete! Check the 'output' directory for:")
    print("  - apostol_with_problems.pdf")
    print("  - apostol_solutions_only.pdf")

if __name__ == "__main__":
    main()
