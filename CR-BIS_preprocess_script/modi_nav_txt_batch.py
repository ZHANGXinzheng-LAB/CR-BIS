import re
import os

def parse_line(line):
    """Extract tilt angle and micrograph info from a line."""
    match = re.match(r'([-\d\.]+) Falcon4_(\d+)_(\d+).tif', line)
    if match:
        tilt_angle, identifier, unknown = match.groups()
        return float(tilt_angle), identifier, int(unknown)  # Keep identifier as a string to maintain leading zeros
    return None

def modify_file(input_path, output_path):
    with open(input_path, 'r') as file:
        lines = file.readlines()
    
    # Parse lines and extract relevant data
    data = [parse_line(line.strip()) + (line.strip(),) for line in lines if parse_line(line.strip())]
    
    # Sort by identifier (#####)
    data.sort(key=lambda x: int(x[1]))  # Convert to int for sorting but keep original string
    
    # Modify '?' column
    for i, (tilt_angle, identifier, unknown, original_line) in enumerate(data):
        new_unknown = 1 if i < 5 else unknown + 1    # unknown + 1 for Falcon4; + 0 for K3
        data[i] = (tilt_angle, identifier, new_unknown, f"{tilt_angle} Falcon4_{identifier}_{new_unknown}.mrc")
    
    # Sort by tilt angle
    data.sort(key=lambda x: x[0])
    
    # Write output
    with open(output_path, 'w') as file:
        for _, _, _, modified_line in data:
            file.write(modified_line + '\n')

def batch_process(folder_path):
    """Process all .txt files in the given folder."""
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            input_path = os.path.join(folder_path, filename)
            output_path = os.path.join(folder_path, "modified_" + filename)
            modify_file(input_path, output_path)

# Example usage
folder_path = "."  # Change this to the actual folder path
batch_process(folder_path)

