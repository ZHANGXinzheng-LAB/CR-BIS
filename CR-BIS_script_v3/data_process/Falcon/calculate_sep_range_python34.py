import struct, os, re, json, argparse, sys


def array_to_json(json_arrays, out_json_file):
    if os.path.exists(out_json_file):
        os.remove(out_json_file)
    
    # 创建字典到字典
    data_dict = {name: arr for name, arr in json_arrays}
    
    # 写入JSON文件
    with open(out_json_file, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=4)

def out_json_path(file_path):
    if file_path.lower().endswith(".eer"):
        new_path = file_path[:-4]  # 从末尾去掉4个字符（.eer）
    else:
        new_path = file_path  # 如果没有.eer扩展名，保持原样

    # 加上_json
    new_path += "_json"
    return new_path

def show_separate_info(file_path, out_json_file, threshold, initial_blank, min_sep):
    try:
        frame_start = []
        data_start = []
        data_length = []
        tag_start = []
        tag_length = []
        dose = []
        tag0_start = []  # 初始化避免未定义引用
        tag0_length = []

        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f_in:
            # 检查文件头
            header = f_in.read(8)
            if len(header) < 8:
                print("Error: header too short!")
                return False, []
            byte_order = header[0:2]
            if byte_order == b'II':
                format_char = '<'  # 小端Intel
            elif byte_order == b'MM':
                format_char = '>'  # 大端Motorola
            else:
                print("Error: byte order not right!")
                return False, []
            version = struct.unpack("{0}H".format(format_char), header[2:4])[0]
            if version == 43:
                offset = struct.unpack("{0}H".format(format_char), header[4:6])[0]
            else:
                print("Error: not EER format!")
                return False, []
            
            # 读取帧起始位置
            while offset < file_size:
                f_in.seek(offset)
                oneframe_start = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                if oneframe_start == 0:
                    break
                frame_start.append(oneframe_start)
                f_in.seek(oneframe_start)
                entry_num = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                
                # tag4 data_start, 8+20*4+12=100
                f_in.seek(oneframe_start + 100)
                onedata_start = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                data_start.append(onedata_start)
                
                # tag7 data_length, 8+20*7+12=160
                f_in.seek(oneframe_start + 160)
                onedata_length = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                data_length.append(onedata_length)
                
                if entry_num == 9:
                    # tag8 tag_length, 8+20*8+4
                    f_in.seek(oneframe_start + 172)
                    onetag_length = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                    tag_length.append(onetag_length)
                    
                    # tag8 tag_start, 8+20*8+12
                    f_in.seek(oneframe_start + 180)
                    onetag_start = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                    tag_start.append(onetag_start)
                    
                    # next frame_start, 8+20*9
                    offset = oneframe_start + 188
                elif entry_num == 10:
                    # tag8 tag0_length, 8+20*8+4
                    f_in.seek(oneframe_start + 172)
                    tag0_length_val = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                    tag0_length.append(tag0_length_val)
                    
                    # tag8 tag0_start, 8+20*8+12
                    f_in.seek(oneframe_start + 180)
                    tag0_start_val = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                    tag0_start.append(tag0_start_val)
                    
                    # tag9 tag_length, 8+20*9+4
                    f_in.seek(oneframe_start + 192)
                    onetag_length = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                    tag_length.append(onetag_length)
                    
                    # tag9 tag_start, 8+20*9+12
                    f_in.seek(oneframe_start + 200)
                    onetag_start = struct.unpack("{0}Q".format(format_char), f_in.read(8))[0]
                    tag_start.append(onetag_start)
                    
                    # next frame_start, 8+20*10
                    offset = oneframe_start + 208
                
                # 从XML格式的tag中读取每帧的剂量
                f_in.seek(onetag_start)
                XML_decode = f_in.read(onetag_length).decode('latin-1', errors='replace')
                XML_match = re.search(r'<item name="dose" unit="e/pixel">([\d.]+)</item>', XML_decode)
                if XML_match:
                    dose.append(float(XML_match.group(1)))
            
            # 将所有帧起始信息保存到out_json_file
            json_arrays = [
                ("frame_start", frame_start),
                ("data_start", data_start),
                ("data_length", data_length),
                ("tag_start", tag_start),
                ("tag_length", tag_length),
                ("dose", dose),
                ("tag0_start", tag0_start),
                ("tag0_length", tag0_length),
                ("format_char", format_char),
                ("file_size", file_size),
            ]
            array_to_json(json_arrays, out_json_file)
            
            # 检查帧起始信息是否正确
            if tag0_start:  # 避免空列表访问
                f_in.seek(tag0_start[0])
                XML_decode = f_in.read(tag0_length[0]).decode('latin-1', errors='replace')
                XML_match = re.search(r'<item name="numberOfFrames">(\d+)</item>', XML_decode)
                if XML_match:
                    frame_num = XML_match.group(1)
                    if int(frame_num) > len(dose):
                        return False, []
            
            # 从空白帧中分离出真实帧
            has_above = any(num > threshold for num in dose)
            has_below_or_equal = any(num <= threshold for num in dose)
            has_both_categories = has_above and has_below_or_equal
            if not has_both_categories:
                return False, []
            
            # 分离数据帧区域
            original_intervals = []
            blank_ranges = []
            sep_frame_nums = []
            in_interval = False
            current_start = 0
                        
            for i, num in enumerate(dose):
                # Falcon4i的第一个空白帧结束于200；Falcon4结束于50
                if num > threshold and i > initial_blank:
                    if not in_interval:
                        current_start = i
                        in_interval = True
                elif num < threshold:
                    if in_interval:
                        original_intervals.append((current_start, i - 1))
                        in_interval = False
            
            if in_interval:
                original_intervals.append((current_start, len(dose) - 1))
                sep_frame_nums.append(len(dose) - 1 - current_start)
                
            candidate_intervals = []
            current_start = 0
            current_end = 0
            for s, e in original_intervals:
                original_length = e - s + 1
                if original_length < min_sep:
                    continue
                current_start = s
                blank_ranges.append(current_start - current_end)
                candidate_intervals.append((s, e))
                current_end = e
                sep_frame_nums.append(current_end - current_start)
            
            starts = [s for s, e in candidate_intervals]
            ends = [e for s, e in candidate_intervals]
            
            frame_num = len(dose)
            sep_num = len(starts)
            if sep_num == 0:
                return False, []
                
            start_gap = starts[0]
            end_gap = len(dose) - ends[-1]
            blank_min = min(blank_ranges[1:]) if len(blank_ranges) > 1 else 0
            blank_max = max(blank_ranges[1:]) if len(blank_ranges) > 1 else 0
            sep_frame_num_min = min(sep_frame_nums) if sep_frame_nums else 0
            sep_frame_num_max = max(sep_frame_nums) if sep_frame_nums else 0
            
            # 替换f-string为format格式
            print("{}: {} frames separate into {} file. First file starts at {}, last file ends at {}; ".format(
                file_path, frame_num, sep_num, start_gap, end_gap
            ))
            print("min gap between files is {}, max gap is {}; ".format(blank_min, blank_max))
            print("min frame number in each file is {}, max is {}".format(sep_frame_num_min, sep_frame_num_max))
            
            output = [start_gap, blank_min, blank_max, end_gap]
            json_arrays = [
                ("starts", starts),
                ("ends", ends),
            ]
            path = out_json_file + '_dose_sep'
            array_to_json(json_arrays, path)
            
    except FileNotFoundError:
        print("错误：找不到文件 {}".format(file_path))
        return False, []
    except Exception as e:
        print("处理文件时发生错误: {}".format(str(e)))
        return False, []
    return True, output

def calculate_sep_ranges(input_folder, output_folder, threshold, initial_blank, min_sep):
    if not os.path.isdir(input_folder):
        print("Error: folder '{}' not exist!".format(input_folder))
        return
    try:
        first_ranges = []
        blank_ranges = []
        end_ranges = []
        for root, dirs, files in os.walk(input_folder):
            for filename in files:
                if filename.endswith(".eer_log"):
                    file = filename[:-len(".eer_log")] + ".eer"
                    print(" {} : processing...".format(file))
                    out_json_file = out_json_path(file)
                    out_json_name = os.path.join(output_folder, out_json_file)
                    file_path = os.path.join(root, file)
                    shw_sep_chk, sep_info_output = show_separate_info(file_path, out_json_name, threshold, initial_blank, min_sep)
                    if shw_sep_chk:
                        first_ranges.append(sep_info_output[0])
                        blank_ranges.append(sep_info_output[1])
                        blank_ranges.append(sep_info_output[2])
                        end_ranges.append(sep_info_output[3])
        
        if len(first_ranges) == 0:
            print("no file can be separated according to the threshold {}".format(threshold))
            return
        
        first_range = (min(first_ranges), max(first_ranges))
        blank_range = (min(blank_ranges), max(blank_ranges))
        end_range = (min(end_ranges), max(end_ranges))
        
        print("first_range:{}".format(first_range))
        print("blank_range:{}".format(blank_range))
        print("end_range:{}".format(end_range))
        
    except Exception as e:
        print("Error: {}".format(str(e)))
    return

if __name__ == "__main__":

    first_range = (457, 506)
    blank_range = (60, 95)
    end_range = (300, 400)

    # file_path = r"D:\EM_bck\map_bck\Falcon4i_00001.eer"

    folder = os.path.dirname(os.path.abspath(sys.argv[0]))
    calculate_sep_ranges(folder, folder, 0.0001, 400, 10)
    """
    # input: 
        (1) input folder, 
        (2) json file output folder, 
        (3) separate threshold
        (4) initail blank frame numb
        (5) min frame num for each separation file
    """
