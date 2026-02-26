CR-BIS: Continuous Recording Beam Image Shift Acquisition for Cryo-EM
Version: 2.0
Platform: SerialEM + Python (≥3.4)

Overview
CR-BIS (Continuous Recording Beam Image Shift) is a data acquisition strategy for cryo-EM and cryo-ET that minimizes camera-induced delay and maximizes throughput.
It extends the standard Beam Image Shift (BIS) method by continuously recording multiple target points in a single exposure, enabling up to 2–4× faster single-particle acquisition and ~3× faster tomographic collection without compromising image quality.
This repository provides:
    • SerialEM scripts for CR-BIS data acquisition
    • Python preprocessing tools for frame splitting and metadata generation
    • Example test datasets and reference parameters

Requirements
Hardware
    • Transmission Electron Microscope (e.g., Titan Krios)
    • Direct Electron Detector (tested: Gatan K3, Falcon 4i, Falcon4)
    • SerialEM control computer (Windows)
Software
Component
Version / Notes
SerialEM
≥ 4.1
Python
≥ 3.4
MotionCor2
For frame alignment
Warp / RELION / AreTomo1
Optional downstream processing

Repository Structure
CR-BIS/
│
├── CR-BIS _scripts_v2/
│   ├── Report_Clock_script.txt				# Measure camera delay curve
│   ├──np_81kx_20260112_script.txt
│   		├── parameter                 # Core parameter configuration file
│   		├── take_map                  # Low-mag map acquisition
│   		├── Tomo_group_V_p1          # Pre-alignment script
│   		├── Tomo_group_X             # Main CR-BIS acquisition
│   		├── reset_X                    # Restore microscope settings
│   └── file_checker.py # Additional control for the advance movement of stage
│   
├── data_process/
│   ├── Falcon/		# Basic command lines of preprocess for CR-BIS-Tomo
│   		├── calculate_sep_range_python34.py 	
│			│		# calculate blank frame gap before splitting EER files
│   		├── eer_writer_5_v4_py34.py
│			│		# eer splitting script
│   		├── tomo_log_edit.py
│			│	# updated information from *log_sep.txt file and modifies tomo_log.txt
│   		├── mdoc.py    # generate the .mdoc file for each tilt series
│          └── tomo_log.txt  #  tomo_log.txt example
│   └── K3/ 
│   		├── group_single_point_tif_MotionCorr2_parallel_v2_tiffile.py
│   		├── modi_tif_log,py
│   		├── modi_tomo_log.py
│          ├── mdoc.py
│          └── tomo_log.txt  #  tomo_log.txt example
└── CR-BIS_User_Guide_v2.0.pdf		# Full illustrated manual
    

Basic Workflow
Part 1 — Pre-Calibration
    1. Use Report_Clock_script.txt to measure total record time vs. exposure setting time.
    2. Determine total exposure formula for your detector model (see guide).
Part 2 — Data Acquisition in SerialEM
    1. Configure parameters in parameter.txt.
    2. Acquire low-magnification maps (take_map.txt).
    3. Select target points in Navigator.
    4. Run sequentially:
        ◦ Tomo_group_V_p1.txt (pre-alignment)
        ◦ Tomo_group_X.txt (CR-BIS data acquisition)
Part 3 — Preprocessing
    1. For TIF data:
    2. python3 group_single_point_tif_MotionCorr2_parallel_v2_tiffile.py /path/to/raw_data
    3. For EER data: python3 eer_writer_5_v4_py34.py frame_num
    4. For Cryo-ET: generate .mdoc files based on tomo_log.txt using mdoc.py.
