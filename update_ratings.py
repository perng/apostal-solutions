import re

# Read the file
with open('apostol/ch1.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match problembox with emoji ratings
pattern = r'\\begin\{problembox\}\[([^\\]+)\\emoji\{star\}:([0-9.]+)\\emoji\{thinking-face\}:([0-9.]+)\]'

# Function to replace each match
def replace_match(match):
    problem_name = match.group(1)
    importance = match.group(2)
    difficulty = match.group(3)
    return f'\\begin{{problembox}}[{problem_name}]\n\\problemrating{{{importance}}}{{{difficulty}}}'

# Replace all matches
updated_content = re.sub(pattern, replace_match, content)

# Write back to file
with open('apostol/ch1.tex', 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("Updated all problem ratings in ch1.tex")
