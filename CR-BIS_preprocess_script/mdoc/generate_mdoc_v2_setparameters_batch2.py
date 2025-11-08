import re
import os
import argparse

def parse_nav_file(nav_file):
    entries = []
    pattern = re.compile(r"Falcon4_(\d+)_(\d+).tif")
    
    with open(nav_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                angle, filename = parts
                match = pattern.search(filename)
                if match:
                    num = int(match.group(1))
                    suffix = int(match.group(2))  # Preserve the suffix (_4_ or _1_)
                    entries.append((num, suffix, float(angle), filename))
    
    return sorted(entries, key=lambda x: (x[0], x[1]))  # Sort by number, then by suffix

def generate_mdoc(entries, output_mdoc, pixel_spacing, voltage, image_size, tilt_axis_angle, binning, num_subframes):
    base_filename = os.path.splitext(os.path.basename(output_mdoc))[0]
    header = f"""
PixelSpacing = {pixel_spacing}
Voltage = {voltage}
ImageFile = {base_filename}
ImageSize = {image_size}
[T = SerialEM: Digitized on TEMname+GIF-K2   ]
[T =     Tilt axis angle = {tilt_axis_angle}, binning = {binning}]
""".strip()
    
    with open(output_mdoc, 'w') as f:
        f.write(header + '\n')
        
        total_frames = len(entries)
        for z, (_, _, angle, filename) in enumerate(entries):
            tif_filename = filename.replace('.tif', '.tif')
            entry = f"""
[ZValue = {z}]
TiltAngle = {angle:.6f}
Magnification = EFTEM 105kx
PixelSpacing = {pixel_spacing}
ImageShift = -1.092003 2.385743
Binning = {binning}
MagIndex = {total_frames}
SubFramePath = {filename.replace('.tif', '.tif')}
NumSubFrames = {num_subframes}
NavigatorLabel = {base_filename}
ExposureDose = {z * 3}
DateTime = 22-Oct-22  12:36:{z+10}
""".strip()
            f.write('\n' + entry + '\n')

def batch_process(folder, pixel_spacing, voltage, image_size, tilt_axis_angle, binning, num_subframes):
    txt_files = [f for f in os.listdir(folder) if f.endswith(".txt")]
    for txt_file in txt_files:
        input_path = os.path.join(folder, txt_file)
        output_mdoc = os.path.splitext(input_path)[0] + ".mdoc"
        data = parse_nav_file(input_path)
        generate_mdoc(data, output_mdoc, pixel_spacing, voltage, image_size, tilt_axis_angle, binning, num_subframes)
        print(f"MDoc file '{output_mdoc}' generated successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process .txt files to generate .mdoc files.")
    parser.add_argument("--folder", required=True, help="Path to the folder containing .txt files")
    parser.add_argument("--pixel_spacing", type=float, default=1.57, help="Pixel spacing value")
    parser.add_argument("--voltage", type=int, default=300, help="Voltage value")
    parser.add_argument("--image_size", type=str, default="4096 4096", help="Image size (width height)")
    parser.add_argument("--tilt_axis_angle", type=float, default=84.6, help="Tilt axis angle")
    parser.add_argument("--binning", type=int, default=1, help="Binning value")
    parser.add_argument("--num_subframes", type=int, default=10, help="Number of subframes")
    args = parser.parse_args()
    
    batch_process(args.folder, args.pixel_spacing, args.voltage, args.image_size, args.tilt_axis_angle, args.binning, args.num_subframes)

