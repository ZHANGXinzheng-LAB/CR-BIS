#!/usr/bin/env python3
# file: modify_tomo_log.py

import argparse
from pathlib import Path


def load_modi_logs(folder: Path) -> dict[str, list[str]]:
    modi_logs = {}
    for path in folder.glob("K2_*_modi.tif_log"):
        key = path.name.replace("_modi.tif_log", "")
        with path.open("r", encoding="utf-8") as f:
            modi_logs[key] = f.readlines()
    return modi_logs


def process_tomo_log(
    tomo_path: Path,
    modi_logs: dict[str, list[str]],
    output_path: Path,
) -> None:
    with tomo_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            output_lines.append(line)
            continue

        if stripped.startswith("tomo_"):
            output_lines.append(line)
            continue

        cols = stripped.split()
        image_name = cols[1]  # K2_#####.tif
        base_name = image_name.replace(".tif", "")

        if base_name in modi_logs:
            output_lines.extend(modi_logs[base_name])
        else:
            cols[1] = f"{base_name}_1.tif"
            output_lines.append(" ".join(cols) + "\n")

    with output_path.open("w", encoding="utf-8") as f:
        f.writelines(output_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Modify tomo_log using modi logs")
    parser.add_argument("--tomo", required=True, help="Path to tomo_log.txt")
    parser.add_argument(
        "--modi-folder",
        required=True,
        help="Folder containing K2_#####_modi.tif_log files",
    )
    args = parser.parse_args()

    tomo_path = Path(args.tomo)
    modi_folder = Path(args.modi_folder)

    if not tomo_path.is_file():
        raise FileNotFoundError(tomo_path)
    if not modi_folder.is_dir():
        raise NotADirectoryError(modi_folder)

    modi_logs = load_modi_logs(modi_folder)

    output_path = tomo_path.with_name("tomo_log_modi.txt")
    process_tomo_log(tomo_path, modi_logs, output_path)

    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()

