import re
from collections import defaultdict

def extract_groups(input_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    groups = defaultdict(lambda: defaultdict(list))
    current_nav = None

    for line in lines:
        line = line.strip()
        if line.startswith("tomo_start at Nav_Item"):
            match = re.search(r"Nav_Item (\d+)", line)
            if match:
                current_nav = match.group(1)
        elif line.startswith("tomo_end"):
            current_nav = None
        elif current_nav:
            match = re.search(r"Falcon4_\d+_(\d+).tif", line) #change the name fit your "output.tif" eg. "K3_\d+_(\d+).tif"
            if match:
                x_value = match.group(1)
                groups[current_nav][x_value].append(line)

    return groups

def save_groups(groups, output_folder):
    for nav, x_groups in groups.items():
        for x, lines in x_groups.items():
            # Sort lines by angle (the first number in the line)
            sorted_lines = sorted(lines, key=lambda line: float(line.split()[0]))
            filename = f"{output_folder}/Nav_{nav}_point_{x}.txt"
            with open(filename, 'w') as f:
                f.write("\n".join(sorted_lines))

# Example Usage
input_file = "tomo_log_extract.txt"  # Replace with your file path
output_folder = "output"  # Replace with your desired output folder

import os
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

groups = extract_groups(input_file)
save_groups(groups, output_folder)
print(f"Extracted, sorted, and saved groups to {output_folder}/")

