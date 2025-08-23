# Apostol Solutions Book - Version Control

This document explains how to generate two different versions of the Apostol solutions book.

## Available Versions

1. **With Problem Statements** - Shows both the problem statement and the solution
2. **Solutions Only** - Shows only the solutions without the problem statements

## How to Generate Both Versions

### Option 1: Using the Python Script (Recommended)

1. Navigate to the `apostol` directory
2. Run the build script:
   ```bash
   python build_versions.py
   ```
3. The script will generate both versions in the `output` directory:
   - `apostol_with_problems.pdf`
   - `apostol_solutions_only.pdf`

### Option 2: Manual Control

1. Open `apostol.tex` in your editor
2. Find the line:
   ```latex
   \showproblemstrue  % Change this to \showproblemsfalse to hide problem statements
   ```
3. To show problem statements: keep `\showproblemstrue`
4. To hide problem statements: change to `\showproblemsfalse`
5. Compile with `pdflatex apostol.tex`

## How It Works

The system uses a LaTeX conditional flag `\ifshowproblems` that controls the definition of the `problembox` environment:

- **When `\showproblemstrue`**: The `problembox` environment displays with a blue background, border, and visible problem statement
- **When `\showproblemsfalse`**: The `problembox` environment shows only the title with a lighter blue background, and the problem content is hidden

### Using the problemstatement Environment

**IMPORTANT**: To properly hide problem statements while keeping titles visible, you MUST wrap the problem content in a `problemstatement` environment:

```latex
\begin{problembox}[1.1: No Largest Prime]
\begin{problemstatement}
Prove that there is no largest prime. (A proof was known to Euclid.)
\end{problemstatement}
\end{problembox}
```

**What happens in each version:**

- **When `\showproblemstrue`**: Shows both the problem name AND the problem statement
- **When `\showproblemsfalse`**: Shows ONLY the problem name, hides the problem statement
- **Solutions** (outside the problembox) are always visible in both versions

**Current chapter files need to be updated** to use the `problemstatement` environment. Without this wrapper, problem statements will always be visible regardless of the flag setting.

## Title Page

The title page automatically shows which version you're generating:
- "With Problem Statements" for the full version
- "Solutions Only" for the solutions-only version

## Table of Contents

Both versions maintain the same table of contents structure, so you can easily navigate to specific problems regardless of which version you're using.

## Notes

- The solutions-only version is useful for students who want to practice problems without seeing the statements first
- The full version is better for reference and study purposes
- Both versions maintain the same page layout and formatting for consistency
