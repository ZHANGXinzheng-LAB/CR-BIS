import os
import tkinter as tk
from tkinter import filedialog
import time


def generate_mdoc():
    try:
        # 获取用户输入的参数
        psize = float(psize_entry.get())
        Tilt_axis_angle = float(Tilt_axis_angle_entry.get())
        magnification = int(magnification_entry.get())
        image_size_x = int(image_size_x_entry.get())
        image_size_y = int(image_size_y_entry.get())

        image_size = f"{image_size_x} {image_size_y}"
        # 获取日志文件所在目录
        data_dir = os.path.dirname(log_file_entry.get())
        tomo_stack_dir = f"{data_dir}/mdocfolder/"
        angle_file = ".mdoc"

        # 创建相关目录，如果不存在的话
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(tomo_stack_dir, exist_ok=True)
        # 清空mdocfolder目录下的所有文件
        for file in os.listdir(tomo_stack_dir):
            file_path = os.path.join(tomo_stack_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        print(f"mdoc files : {tomo_stack_dir}")
        print("running, this may take a few minutes...")

        current_time = int(time.time())

        # 获取tomo_log.txt文件的行数，用于控制循环次数
        log_file_path = log_file_entry.get()
        with open(log_file_path, 'r') as f:
            line_count = sum(1 for _ in f)

        # 用于记录同一tomo_item_num出现的次数，初始化为0
        zvalue_count_dict = {}
        for line_index in range(line_count):
            elements = []
            with open(log_file_path, 'r') as f:
                for index, line in enumerate(f):
                    if index == line_index:
                        elements = line.strip().split()
                        break

            # 判断该行是否为数据行（第二列内容包含”eer“或者”tiff“），不是数据行则跳过
            if len(elements) < 2 or ("eer" not in elements[1] and "tiff" not in elements[1]):
                continue

            tomo_item_num = elements[4]
            if tomo_item_num not in zvalue_count_dict:
                zvalue_count_dict[tomo_item_num] = 0

            add_num = 0
            mdoc_file_path = os.path.join(tomo_stack_dir, f"tomo_NavItem_{tomo_item_num}_{add_num:03d}{angle_file}")
            if not os.path.exists(mdoc_file_path):
                with open(mdoc_file_path, 'w') as mdoc_file:
                    mdoc_file.write(f"PixelSpacing = {psize}\n")
                    mdoc_file.write("Voltage = 300\n")
                    mdoc_file.write(f"ImageFile = tomo_NavItem_{tomo_item_num}\n")
                    mdoc_file.write(f"ImageSize = {image_size}\n")
                    mdoc_file.write("DataMode = 1\n\n")
                    mdoc_file.write(f"[T = SerialEM: Digitized on IBP Titan   ]\n\n")
                    mdoc_file.write(f"[T =     Tilt axis angle = {Tilt_axis_angle}, binning = 1  spot = 6  camera = 4]\n\n")

            with open(mdoc_file_path, 'a') as mdoc_file:
                # 将ZvalueN设置为同一tomo_item_num的出现次数
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

                # 提取tomo_log.txt文件第二列中的文件名作为SubFramePath的值
                file_path_str = elements[1]
                last_separator_index = file_path_str.rfind("\\")  # 在Windows风格路径下查找最后一个反斜杠的位置
                if last_separator_index == -1:
                    last_separator_index = file_path_str.rfind("/")  # 如果没找到反斜杠，尝试查找正斜杠（用于Linux风格路径或混合情况）
                if last_separator_index != -1:
                    file_name = file_path_str[last_separator_index + 1:]  # 提取最后一个分隔符之后的部分作为文件名
                    print(file_name)
                else:
                    file_name = file_path_str
                    print(file_name)
                mdoc_file.write(f"SubFramePath = {file_name}\n")

                new_time = current_time + line_index
                time_struct = time.localtime(new_time)
                formatted_time = time.strftime("%d-%b-%y  %H:%M:%S", time_struct)
                mdoc_file.write(f"DateTime = {formatted_time}\n")
                mdoc_file.write(f"NavigatorLabel = {elements[4]}\n")
                mdoc_file.write("FilterSlitAndLoss = 0 0\n\n")

        print("########################-------Completed----------#############################")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 无论是否出现异常，处理完后自动关闭窗口
        root.destroy()


root = tk.Tk()
root.title("Mdoc Generator")

# 用于输入tomo_log.txt文件的输入框及按钮
log_file_label = tk.Label(root, text="select tomo_log.txt file:")
log_file_label.pack()
log_file_entry = tk.Entry(root)
log_file_entry.pack()
# 打开文件预览后，只显示形如“tomo_log*.txt”的文件
log_file_browse_button = tk.Button(root, text="find", command=lambda: log_file_entry.insert(0, filedialog.askopenfilename(filetypes=[("txt file", "tomo_log*.txt")])))
log_file_browse_button.pack()

# 其他参数的输入框及对应标签
psize_label = tk.Label(root, text="psize (default:2):")
psize_label.pack()
psize_entry = tk.Entry(root)
psize_entry.insert(0, "2")
psize_entry.pack()

Tilt_axis_angle_label = tk.Label(root, text="Tilt_axis_angle (default: 84.6):")
Tilt_axis_angle_label.pack()
Tilt_axis_angle_entry = tk.Entry(root)
Tilt_axis_angle_entry.insert(0, "84.6")
Tilt_axis_angle_entry.pack()

magnification_label = tk.Label(root, text="magnification (default:64000):")
magnification_label.pack()
magnification_entry = tk.Entry(root)
magnification_entry.insert(0, "64000")
magnification_entry.pack()

image_size_x_label = tk.Label(root, text="image_size_x (default:4096):")
image_size_x_label.pack()
image_size_x_entry = tk.Entry(root)
image_size_x_entry.insert(0, "4096")
image_size_x_entry.pack()

image_size_y_label = tk.Label(root, text="image_size_y (default:4096):")
image_size_y_label.pack()
image_size_y_entry = tk.Entry(root)
image_size_y_entry.insert(0, "4096")
image_size_y_entry.pack()

generate_button = tk.Button(root, text="creat mdoc", command=generate_mdoc)
generate_button.pack()

root.mainloop()