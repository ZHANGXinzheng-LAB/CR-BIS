import re
import os
import subprocess
from pathlib import Path

def process_flat_tilt_file(input_file):
    base_dir = Path(input_file).parent
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        return []

    sorted_lines = sorted(lines, key=lambda l: float(l.split()[0]))
    return [str(base_dir / line.split()[1]) for line in sorted_lines]

def create_tilt_stack(image_list, output_stack_path):
    command = ["newstack"] + image_list + [str(output_stack_path)]
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("newstack failed:", e.stderr)

def batch_process_tilt_series(input_folder, output_folder):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    txt_files = list(input_path.glob("*.txt"))

    for txt_file in txt_files:
        image_list = process_flat_tilt_file(txt_file)
        if image_list:
            stack_name = txt_file.with_suffix(".mrc").name
            output_stack = output_path / stack_name
            create_tilt_stack(image_list, output_stack)
            print(f"Created tilt stack: {output_stack}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch create tilt stacks from sorted tilt series .txt files")
    parser.add_argument("--input_folder", required=True, help="Folder containing input .txt files")
    parser.add_argument("--output_folder", required=True, help="Folder to save .mrc tilt stacks")
    args = parser.parse_args()

    batch_process_tilt_series(args.input_folder, args.output_folder)

