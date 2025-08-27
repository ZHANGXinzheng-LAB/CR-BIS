import re
import argparse

def process_tomo_log(input_file, output_file):
    """
    Processes a tomo log file based on specified renaming rules for image names and angles.

    Parameters:
    - input_file: Path to the input file.
    - output_file: Path to the output file.
    """
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()
        group_lines = []  # Holds lines within a Nav_Item group
        within_group = False  # Tracks if we're within a group

        for line in lines:
            # Start of a new group
            if line.startswith("tomo_start at Nav_Item"):
                if within_group and group_lines:
                    # Process the previous group
                    process_group(group_lines, outfile)
                within_group = True
                group_lines = []
                outfile.write(line)  # Write "tomo_start" to output
                continue

            # End of a group or start of the next group
            if line.startswith("tomo_end at Nav_Item") or line.startswith("tomo_start at Nav_Item"):
                if within_group and group_lines:
                    # Process the current group
                    process_group(group_lines, outfile)
                within_group = False
                group_lines = []
                outfile.write(line)  # Write "tomo_end" to output if present
                if line.startswith("tomo_start"):
                    outfile.write(line)  # Write the new "tomo_start" for the next group
                continue

            # Regular line within a group
            if within_group:
                group_lines.append(line)

def process_group(group_lines, outfile):
    """
    Processes a single group of lines and writes the output to the file.

    Parameters:
    - group_lines: Lines within the current group.
    - outfile: Open file object to write the results.
    """
    previous_degree = None
    next_degree = None
    current_angle_lines = []

    for i, line in enumerate(group_lines):
        columns = line.split()
        if len(columns) > 1:
            degree = columns[0]
            image_name_match = re.search(r"(Falcon4_\d+)\.eer", line)    
            if image_name_match:
                image_name = image_name_match.group(1)

                # Look ahead to find the next degree
                if i + 1 < len(group_lines):
                    next_line = group_lines[i + 1]
                    next_columns = next_line.split()
                    next_degree = next_columns[0] if len(next_columns) > 1 else None
                else:
                    next_degree = None

                if previous_degree is None:
                    # First line in the group
                    previous_degree = degree
                    current_angle_lines.append((degree, image_name))
                elif degree == previous_degree:
                    # Same angle as the previous line
                    current_angle_lines.append((degree, image_name))
                elif degree != previous_degree:
                    if degree == next_degree:
                        # Restart for new angle
                        output_lines_with_names(current_angle_lines, outfile)
                        previous_degree = degree
                        current_angle_lines = [(degree, image_name)]
                    else:
                        # Unique angle; repeat 28 times with suffix
                        output_lines_with_names(current_angle_lines, outfile)
                        output_repeat_lines(degree, image_name, outfile)
                        previous_degree = degree
                        current_angle_lines = []

    # Process any remaining lines
    if current_angle_lines:
        output_lines_with_names(current_angle_lines, outfile)

def output_lines_with_names(angle_lines, outfile):
    """
    Outputs lines with modified names based on the degree.

    Parameters:
    - angle_lines: Lines with the same degree to be processed.
    - outfile: Open file object to write the results.
    """
    for i, (degree, image_name) in enumerate(angle_lines, start=1):
        outfile.write(f"{degree} {image_name}_{i}.tif\n")

def output_repeat_lines(degree, image_name, outfile, repeat_count=28):
    """
    Outputs a single line repeated `repeat_count` times with incremented suffixes.

    Parameters:
    - degree: The degree to output.
    - image_name: Base image name to modify.
    - outfile: Open file object to write the results.
    - repeat_count: Number of times to repeat the line.
    """
    for i in range(1, repeat_count + 1):
        outfile.write(f"{degree} {image_name}_{i}.tif\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a tomo log file to rename images.")
    parser.add_argument("--input", required=True, help="Path to the input file.")
    parser.add_argument("--output", required=True, help="Path to the output file.")
    args = parser.parse_args()

    process_tomo_log(args.input, args.output)

