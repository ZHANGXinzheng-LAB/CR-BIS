#!/usr/bin/env python3
# file: modify_k2_logs.py

import argparse
from pathlib import Path


def process_log_file(log_path: Path) -> None:
    base_name = log_path.name.replace(".tif_log", "")
    output_path = log_path.with_name(f"{base_name}_modi.tif_log")

    with log_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    modified_lines = []
    line_number = 1

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        cols = stripped.split()
        insert_value = f"{base_name}_{line_number}.tif"

        new_cols = [cols[0], insert_value] + cols[1:]
        modified_lines.append(" ".join(new_cols) + "\n")

        line_number += 1

    with output_path.open("w", encoding="utf-8") as f:
        f.writelines(modified_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Modify K2 tif_log files")
    parser.add_argument(
        "--folder",
        required=True,
        help="Path to folder containing K2_#####.tif_log files",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"Invalid folder: {folder}")

    log_files = sorted(folder.glob("K2_*.tif_log"))
    if not log_files:
        print("No matching log files found.")
        return

    for log_file in log_files:
        process_log_file(log_file)
        print(f"Processed: {log_file.name}")


if __name__ == "__main__":
    main()

