import tifffile as tiff
import numpy as np
import os
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor
import time

def is_black_frame(frame, threshold=0.01):
    """
    Check if a frame is black by calculating its average intensity and comparing to a given threshold.
    """
    avg_intensity = np.mean(frame)
    print(f"Frame intensity: {avg_intensity}")  # Debug: Print the average intensity of the frame
    return avg_intensity < threshold

def process_frame_group(frames, output_prefix, group_index, motioncorr2_path, gain_file, pix_size, kv, gpu_list, bft, fm_dose, patch=None):
    """
    Save a group of frames into a TIFF file and optionally run MotionCorr2.
    """
    tiff_output_path = f"{output_prefix}_{group_index + 1}.tif"

    # Save the grouped frames
    with tiff.TiffWriter(tiff_output_path) as tif:
        for frame in frames:
            tif.write(frame, photometric="minisblack")

    print(f"Saved group {group_index + 1} to {tiff_output_path}")

    # Run MotionCorr2 on the saved TIFF if the path is provided
    if motioncorr2_path:
        mrc_output_path = f"{output_prefix}_{group_index + 1}.mrc"
        gpu_index = gpu_list[group_index % len(gpu_list)]  # Use multiple GPUs in a round-robin fashion
        motioncorr2_cmd = [
            motioncorr2_path,
            "-InTiff", tiff_output_path,
            "-OutMrc", mrc_output_path,
            "-Bft", str(bft),
            "-FmDose", str(fm_dose),
            "-PixSize", str(pix_size),
            "-kV", str(kv),
            "-Gpu", str(gpu_index)
        ]

        if patch:
            motioncorr2_cmd.extend(["-Patch", str(patch[0]), str(patch[1])])

        if gain_file:
            motioncorr2_cmd.extend(["-gain", gain_file])

        print(f"Running MotionCorr2: {' '.join(motioncorr2_cmd)}")
        try:
            subprocess.run(motioncorr2_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"MotionCorr2 failed with error: {e}")
        print(f"Motion correction completed for {tiff_output_path}, output saved to {mrc_output_path}")

def group_frames_by_blackness(input_tif, threshold=0.01, motioncorr2_path=None, gain_file=None, pix_size=0.76, kv=300, gpu_list=[0], bft=500, fm_dose=1, patch=None):
    """
    Process a multi-frame TIFF file, identify black frames, and group non-black frames into separate TIFF files.

    Args:
        input_tif (str): Path to the input multi-frame TIFF file.
        threshold (float): Threshold to consider a frame as black.
        motioncorr2_path (str): Path to the MotionCorr2 executable.
        gain_file (str): Path to the gain reference file.
        pix_size (float): Pixel size in angstroms.
        kv (int): Acceleration voltage in kV.
        gpu_list (list): List of GPU indices to use.
        bft (int): B-factor for motion correction.
        fm_dose (float): Frame dose in electrons per pixel.
        patch (tuple): Optional patch size for MotionCorr2 (-Patch parameter).
    """
    output_prefix = os.path.splitext(os.path.basename(input_tif))[0]  # Automatically derive output prefix
    with tiff.TiffFile(input_tif) as tif:
        current_group = []
        group_index = 0

        with ThreadPoolExecutor(max_workers=len(gpu_list)) as executor:
            futures = []

            for frame_index, page in enumerate(tif.pages):
                try:
                    frame = page.asarray()
                    print(f"Processing frame {frame_index + 1}...")

                    if is_black_frame(frame, threshold):
                        print(f"Frame {frame_index + 1} is black.")
                        if current_group:
                            frames_copy = current_group.copy()
                            future = executor.submit(
                                process_frame_group,
                                frames_copy,
                                output_prefix,
                                group_index,
                                motioncorr2_path,
                                gain_file,
                                pix_size,
                                kv,
                                gpu_list,
                                bft,
                                fm_dose,
                                patch
                            )
                            futures.append(future)
                            group_index += 1
                            current_group = []
                    else:
                        print(f"Frame {frame_index + 1} is not black.")
                        current_group.append(frame)

                except Exception as e:
                    print(f"Error processing frame {frame_index + 1}: {e}. Skipping.")
                    continue

            # Process the last group if it exists
            if current_group:
                frames_copy = current_group.copy()
                future = executor.submit(
                    process_frame_group,
                    frames_copy,
                    output_prefix,
                    group_index,
                    motioncorr2_path,
                    gain_file,
                    pix_size,
                    kv,
                    gpu_list,
                    bft,
                    fm_dose,
                    patch
                )
                futures.append(future)

            # Wait for all futures to complete
            for future in futures:
                future.result()

def batch_process_tiffs(input_directory, threshold=0.01, motioncorr2_path=None, gain_file=None, pix_size=0.76, kv=300, gpu_list=[0], bft=500, fm_dose=1, patch=None):
    """
    Batch process TIFF files in a directory, processing them one by one as they appear.

    Args:
        input_directory (str): Path to the directory containing TIFF files.
        threshold (float): Threshold to consider a frame as black.
        motioncorr2_path (str): Path to the MotionCorr2 executable.
        gain_file (str): Path to the gain reference file.
        pix_size (float): Pixel size in angstroms.
        kv (int): Acceleration voltage in kV.
        gpu_list (list): List of GPU indices to use.
        bft (int): B-factor for motion correction.
        fm_dose (float): Frame dose in electrons per pixel.
        patch (tuple): Optional patch size for MotionCorr2 (-Patch parameter).
    """
    processed_files = set()
    last_activity_time = time.time()

    while True:
        all_files = sorted([f for f in os.listdir(input_directory) if f.endswith(".tif")])
        for filename in all_files:
            if filename not in processed_files:
                filepath = os.path.join(input_directory, filename)

                # Check if the next file in the sorted list is present (indicating the current file is complete)
                current_index = all_files.index(filename)
                if current_index + 1 < len(all_files):
                    next_file = all_files[current_index + 1]
                else:
                    # If no new file appears for more than 15 minutes, process the last file and exit
                    if time.time() - last_activity_time > 60:  # 15 minutes in seconds
                        print(f"No new file detected for 15 minutes. Processing the last file: {filepath}.")
                        group_frames_by_blackness(
                            filepath,
                            threshold=threshold,
                            motioncorr2_path=motioncorr2_path,
                            gain_file=gain_file,
                            pix_size=pix_size,
                            kv=kv,
                            gpu_list=gpu_list,
                            bft=bft,
                            fm_dose=fm_dose,
                            patch=patch
                        )
                        return
                    else:
                        print(f"Waiting for next file to appear after {filename}.")
                        time.sleep(5)  # Sleep before re-checking
                        continue

                print(f"Processing file: {filepath}")
                group_frames_by_blackness(
                    filepath,
                    threshold=threshold,
                    motioncorr2_path=motioncorr2_path,
                    gain_file=gain_file,
                    pix_size=pix_size,
                    kv=kv,
                    gpu_list=gpu_list,
                    bft=bft,
                    fm_dose=fm_dose,
                    patch=patch
                )
                processed_files.add(filename)
                last_activity_time = time.time()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process multiple TIFF files to remove black frames, group non-black frames, and run MotionCorr2.")
    parser.add_argument("input_directory", type=str, help="Path to the directory containing TIFF files.")
    parser.add_argument("--threshold", type=float, default=0.01, help="Threshold to consider a frame as black (default: 0.01).")
    parser.add_argument("--motioncorr2_path", type=str, help="Path to the MotionCorr2 executable.", required=False)
    parser.add_argument("--gain_file", type=str, help="Path to the gain reference file.", required=False)
    parser.add_argument("--pix_size", type=float, default=0.76, help="Pixel size in angstroms (default: 0.76).")
    parser.add_argument("--kv", type=int, default=300, help="Acceleration voltage in kV (default: 300).")
    parser.add_argument("--gpu_list", type=int, nargs='+', default=[0], help="List of GPU indices to use (default: [0]).")
    parser.add_argument("--bft", type=int, default=500, help="B-factor for motion correction (default: 500).")
    parser.add_argument("--fm_dose", type=float, default=1, help="Frame dose in electrons per pixel (default: 1).")
    parser.add_argument("--patch", type=int, nargs=2, help="Patch size for MotionCorr2 (e.g., --patch 5 5).", required=False)

    args = parser.parse_args()

    batch_process_tiffs(
        args.input_directory,
        threshold=args.threshold,
        motioncorr2_path=args.motioncorr2_path,
        gain_file=args.gain_file,
        pix_size=args.pix_size,
        kv=args.kv,
        gpu_list=args.gpu_list,
        bft=args.bft,
        fm_dose=args.fm_dose,
        patch=args.patch
    )

