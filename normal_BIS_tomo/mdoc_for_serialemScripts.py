# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 20:56:11 2025

@author: ZY
"""

import os
import time
import argparse


def is_data_line(line):
    """判断一行是否为数据行（第二列包含eer\mrc或tiff）"""
    elements = line.strip().split()
    return len(elements) >= 2 and ("eer" in elements[1] or "tiff" in elements[1] or "mrc" in elements[1] or "tif" in elements[1])


def find_line_numbers(log_file_path):
    """从后向前查找，确定firstlineNo和lastlineNo"""
    with open(log_file_path, 'r') as f:
        lines = f.readlines()
    
    line_count = len(lines)
    firstlineNo = None
    lastlineNo = None
    found_last = False
    
    # 从最后一行向前遍历
    for i in range(line_count - 1, -1, -1):
        current_line = lines[i]
        
        if not is_data_line(current_line):
            # 检查前一行是否为数据行
            if i > 0 and is_data_line(lines[i-1]):
                if not found_last:
                    # 找到lastlineNo
                    lastlineNo = i 
                    found_last = True            
                else:
                    # 找到firstlineNo
                    firstlineNo = i
                    break
            elif found_last:
                # 找到firstlineNo
                firstlineNo = i
                break
    
    # 处理边界情况：如果只找到lastlineNo而没有找到firstlineNo
    if found_last and firstlineNo is None:
        firstlineNo = 0  # 从第一行开始
    
    return firstlineNo, lastlineNo


def generate_mdoc(log_file_path, psize, tilt_axis_angle, magnification, 
                 image_size_x, image_size_y):
    try:
        # 转换参数类型
        psize = float(psize)
        tilt_axis_angle = float(tilt_axis_angle)
        magnification = int(magnification)
        image_size_x = int(image_size_x)
        image_size_y = int(image_size_y)

        image_size = f"{image_size_x} {image_size_y}"
        # 获取日志文件所在目录
        data_dir = os.path.dirname(log_file_path)
        tomo_stack_dir = f"{data_dir}/mdocfolder/"
        
        # 创建目录（如果不存在）
        os.makedirs(tomo_stack_dir, exist_ok=True)

        # 生成时间戳（本次运行所有文件共用）
        timestamp = time.strftime("%Y%m%d%H%M%S")
        angle_file = f".mdoc"

        print(f"mdoc files will be saved to: {tomo_stack_dir}")
        print("Running, this may take a few minutes...")

        # 查找需要处理的行范围
        firstlineNo, lastlineNo = find_line_numbers(log_file_path)
        
        if firstlineNo is None or lastlineNo is None:
            print("No valid data lines found in the log file")
            return
        
        if firstlineNo > lastlineNo:
            print("Invalid line numbers found, swapping them")
            firstlineNo, lastlineNo = lastlineNo, firstlineNo

        print(f"Processing lines from {firstlineNo} to {lastlineNo}")

        # 读取所有行以便处理
        with open(log_file_path, 'r') as f:
            lines = f.readlines()

        # 用于记录同一tomo_item_num出现的次数
        zvalue_count_dict = {}
        
        # 按从上到下的顺序处理指定范围的行
        for line_index in range(firstlineNo, lastlineNo + 1):
            line = lines[line_index]
            elements = line.strip().split()
            
            # 再次检查是否为数据行（确保安全）
            if not is_data_line(line):
                continue

            tomo_item_num = elements[4]
            if tomo_item_num not in zvalue_count_dict:
                zvalue_count_dict[tomo_item_num] = 0

            # 构建带时间戳的文件名
            add_num = 0
            mdoc_filename = f"tomo_NavItem_{tomo_item_num}_{add_num:03d}_{timestamp}{angle_file}"
            mdoc_file_path = os.path.join(tomo_stack_dir, mdoc_filename)

            # 如果文件不存在，写入头部信息
            if not os.path.exists(mdoc_file_path):
                with open(mdoc_file_path, 'w') as mdoc_file:
                    mdoc_file.write(f"PixelSpacing = {psize}\n")
                    mdoc_file.write("Voltage = 300\n")
                    mdoc_file.write(f"ImageFile = tomo_NavItem_{tomo_item_num}\n")
                    mdoc_file.write(f"ImageSize = {image_size}\n")
                    mdoc_file.write("DataMode = 1\n\n")
                    mdoc_file.write(f"[T = SerialEM: Digitized on IBP Titan   ]\n\n")
                    mdoc_file.write(f"[T =     Tilt axis angle = {tilt_axis_angle}, binning = 1  spot = 6  camera = 4]\n\n")

            # 追加ZValue部分
            with open(mdoc_file_path, 'a') as mdoc_file:
                ZvalueN = zvalue_count_dict[tomo_item_num]
                mdoc_file.write(f"[ZValue = {ZvalueN}]\n")
                mdoc_file.write("MinMaxMean = 0 0 0\n")
                mdoc_file.write(f"TiltAngle = {elements[0]}\n")
                mdoc_file.write("StagePosition = 0.0 0.0\n")
                mdoc_file.write("StageZ = 0.0\n")
                mdoc_file.write(f"Magnification = {magnification}\n")
                mdoc_file.write("Intensity = 0.0\n")
                mdoc_file.write("ExposureDose = 0\n")
                mdoc_file.write("DoseRate = 0.0\n")
                mdoc_file.write(f"PixelSpacing = {psize}\n")
                mdoc_file.write("SpotSize = 0\n")
                mdoc_file.write("Defocus = 0.0\n")
                mdoc_file.write(f"ImageShift = {elements[2]} {elements[3]}\n")
                mdoc_file.write("RotationAngle = 0\n")
                mdoc_file.write("ExposureTime = 0\n")
                mdoc_file.write("Binning = 0\n")
                mdoc_file.write("CameraIndex = 0\n")
                mdoc_file.write("DividedBy2 = 0\n")
                mdoc_file.write("OperatingMode = 0\n")
                mdoc_file.write("MagIndex = 0\n")
                mdoc_file.write("LowDoseConSet = 0\n")
                mdoc_file.write("CountsPerElectron = 0\n")
                mdoc_file.write("TargetDefocus = 0\n")
                mdoc_file.write("NumSubFrames = 0\n")
                mdoc_file.write("FrameDosesAndNumber = 0 0\n")

                zvalue_count_dict[tomo_item_num] += 1

                # 提取文件名作为SubFramePath的值
                file_path_str = elements[1]
                # 查找最后一个路径分隔符
                last_sep_idx = max(file_path_str.rfind("\\"), file_path_str.rfind("/"))
                if last_sep_idx != -1:
                    file_name = file_path_str[last_sep_idx + 1:]
                    print(f"Processing file: {file_name}")
                else:
                    file_name = file_path_str
                    print(f"Using full path as filename: {file_name}")
                mdoc_file.write(f"SubFramePath = {file_name}\n")

                # 生成时间
                current_time = int(time.time()) + (line_index)
                time_struct = time.localtime(current_time)
                formatted_time = time.strftime("%d-%b-%y  %H:%M:%S", time_struct)
                mdoc_file.write(f"DateTime = {formatted_time}\n")
                mdoc_file.write(f"NavigatorLabel = {elements[4]}\n")
                mdoc_file.write("FilterSlitAndLoss = 0 0\n\n")

        print("########################-------Completed----------#############################")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='Generate mdoc files from tomo log.')
    parser.add_argument('log_file', help='Path to the tomo_log.txt file')
    parser.add_argument('--psize', default=2, help='psize value (default: 2)')
    parser.add_argument('--tilt-axis', default=84.6, help='Tilt axis angle (default: 84.6)')
    parser.add_argument('--magnification', default=64000, help='Magnification (default: 64000)')
    parser.add_argument('--image-size-x', default=4096, help='Image size X (default: 4096)')
    parser.add_argument('--image-size-y', default=4096, help='Image size Y (default: 4096)')
    # parser = argparse.ArgumentParser(description='Generate mdoc files from tomo log.')
    # parser.add_argument('log_file', help='Path to the tomo_log.txt file')
    # parser.add_argument('psize', nargs='?', default=2.02, help='psize value (default: 2)')
    # parser.add_argument('tilt_axis', nargs='?', default=84.66, help='Tilt axis angle (default: 84.6)')
    # parser.add_argument('magnification', nargs='?', default=64000, help='Magnification (default: 64000)')
    # parser.add_argument('image_size_x', nargs='?', default=4096, help='Image size X (default: 4096)')
    # parser.add_argument('image_size_y', nargs='?', default=4096, help='Image size Y (default: 4096)')

    args = parser.parse_args()
    print("python start!!!!!!!!!!")
    # 打印参数值用于验证
    print(f"接收的参数:")
    print(f"log_file: {args.log_file}")
    print(f"psize: {args.psize}")
    print(f"tilt_axis: {args.tilt_axis}")
    print(f"magnification: {args.magnification}")
    print(f"image_size_x: {args.image_size_x}")
    print(f"image_size_y: {args.image_size_y}")
    # 调用生成函数
    generate_mdoc(
        log_file_path=args.log_file,
        psize=args.psize,
        tilt_axis_angle=args.tilt_axis,
        magnification=args.magnification,
        image_size_x=args.image_size_x,
        image_size_y=args.image_size_y
    )


    #generate_mdoc(r"C:\Users\ZY\Desktop\test\tomo_log.txt",  2,  84.6,  64000,  4096,  4096)
    # generate_mdoc(
    #     log_file_path=r"C:\Users\ZY\Desktop\test\tomo_log.txt",
    #     psize=2,
    #     tilt_axis_angle=84.6,
    #     magnification=64000,
    #     image_size_x=4096,
    #     image_size_y=4096
    # )
