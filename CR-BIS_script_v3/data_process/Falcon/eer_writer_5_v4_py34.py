import struct, os, re, json, argparse, binascii, sys, time

def check_tiff_info(file_path):
    file_size = os.path.getsize(file_path)

    format_char = '<'  # 小端
    version = 43  #BigTIFF
    offset = 8  #第一个IFD的偏移量
    try:
        with open(file_path, 'rb') as f:
            # 读取文件头前8个字节（足够判断TIFF版本和指针大小）
            header = f.read(8)
            
            if len(header) < 8:
                print("错误:文件太小,不是有效的TIFF文件")
                return False,format_char,version,offset,file_size
            
            # 解析字节顺序（前2个字节）
            byte_order = header[0:2]
            if byte_order == b'II':
                #endian = "小端字节序 (Intel)"
                format_char = '<'  # 小端
            elif byte_order == b'MM':
                #endian = "大端字节序 (Motorola)"
                format_char = '>'  # 大端
            else:
                print("错误:无效的TIFF文件标识,找到 {} 而非 II 或 MM".format(binascii.hexlify(byte_order).decode('ascii')))
                return False,format_char,version,offset,file_size
            
            # 解析版本号（接下来2个字节）
            version = struct.unpack(format_char + "H", header[2:4])[0]
            
            # 解析偏移量（接下来4或8个字节，取决于TIFF版本）
            if version == 42:
                # 标准TIFF，使用32位偏移量（4字节）
                offset = struct.unpack(format_char + "I", header[4:8])[0]
                #pointer_size = "32bit (4字节)"
                #tiff_version = "标准TIFF (TIFF 6.0)"
            elif version == 43:
                # BigTIFF，使用64位偏移量（8字节）
                # 需要再读取4个字节才能获取完整的8字节偏移量
                #offset_bytes = header[4:8] + f.read(4)
                offset = struct.unpack(format_char + "H", header[4:6])[0]
                #offset = struct.unpack(f"{format_char}Q", offset_bytes)[0]
                #pointer_size = "64bit (8字节)"
                #tiff_version = "BigTIFF"
            else:
                print("错误:未知的TIFF版本号 {}".format(version))
                return False,format_char,version,offset,file_size
            
    except FileNotFoundError:
        print("错误：找不到文件 {}".format(file_path))
        return False,format_char,version,offset,file_size
    except Exception as e:
        print("处理文件时发生错误: {}".format(str(e)))
        return False,format_char,version,offset,file_size
    
    return True,format_char,version,offset,file_size
            
def read_frame_start(file_path,out_json_file,format_char,offset,file_size):
    frame_start = []
    data_start = []
    data_length = []
    tag_start = []
    tag_length = []
    dose = []
    tag0_start = 100
    tag0_length = 845

    try:
        with open(file_path, 'rb') as f:
            
            while offset < file_size:
                #print(offset)
                f.seek(offset)
                oneframe_start = struct.unpack(format_char + "Q", f.read(8))[0]
                
                if oneframe_start == 0:
                    break
                
                frame_start.append(oneframe_start)
                f.seek(oneframe_start)
                entry_num = struct.unpack(format_char + "Q", f.read(8))[0]
                
                f.seek(oneframe_start+100) #tag4 dsata_start, 8+20*4+12=100
                onedata_start = struct.unpack(format_char + "Q", f.read(8))[0]
                data_start.append(onedata_start)
                
                f.seek(oneframe_start+160) #tag7 dsata_length, 8+20*7+12=160
                onedata_length = struct.unpack(format_char + "Q", f.read(8))[0]
                data_length.append(onedata_length)
                
                if entry_num == 9:
                    f.seek(oneframe_start+172) #tag8 tag_length, 8+20*8+4
                    onetag_length = struct.unpack(format_char + "Q", f.read(8))[0]
                    tag_length.append(onetag_length)
                    
                    f.seek(oneframe_start+180) #tag8 tag_start, 8+20*8+12
                    onetag_start = struct.unpack(format_char + "Q", f.read(8))[0]
                    tag_start.append(onetag_start)
                    
                    offset = oneframe_start+188 #next frame_start, 8+20*9
                elif entry_num == 10:
                    f.seek(oneframe_start+172) #tag8 tag0_length, 8+20*8+4
                    tag0_length = struct.unpack(format_char + "Q", f.read(8))[0]
                    
                    f.seek(oneframe_start+180) #tag8 tag0_start, 8+20*8+12
                    tag0_start = struct.unpack(format_char + "Q", f.read(8))[0]
                    
                    f.seek(oneframe_start+192) #tag9 tag_length, 8+20*9+4
                    onetag_length = struct.unpack(format_char + "Q", f.read(8))[0]
                    tag_length.append(onetag_length)
                    
                    f.seek(oneframe_start+200) #tag9 tag_start, 8+20*9+12
                    onetag_start = struct.unpack(format_char + "Q", f.read(8))[0]
                    tag_start.append(onetag_start)
                    
                    offset = oneframe_start+208 #next frame_start, 8+20*10
                    
                f.seek(onetag_start)  #read dose of each frame from tag of XML format
                XML_decode = f.read(onetag_length).decode('latin-1', errors='replace')
                XML_match = re.search(r'<item name="dose" unit="e/pixel">([\d.]+)</item>',XML_decode)
                if XML_match:
                    dose.append(float(XML_match.group(1)))
                    
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
            print(1)
            #array_to_json(json_arrays,out_json_path)
            array_to_json(json_arrays,out_json_file)
            
            f.seek(tag0_start)
            XML_decode = f.read(tag0_length).decode('latin-1', errors='replace')
            XML_match = re.search(r'<item name="numberOfFrames">(\d+)</item>',XML_decode)
            if XML_match:
                frame_num = XML_match.group(1)
                print(frame_num)
                if int(frame_num) > len(dose):
                    return False
            
    except FileNotFoundError:
        print("错误：找不到文件 {}".format(file_path))
        return False
    except Exception as e:
        print("处理文件时发生错误: {}".format(str(e)))
        return False
        
#    return True,frame_start,data_start,data_length,tag_start,tag_length,dose
    return True

def array_to_json(json_arrays,out_json_file):
    if os.path.exists(out_json_file):
        os.remove(out_json_file)
    
    # 创建字典到字典
    data_dict = {name: arr for name, arr in json_arrays}
    
    # 写入JSON文件
    with open(out_json_file, 'w', encoding='utf-8') as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=4)

def rewrite_65001(file_path,out_json_file,modify_item):
    """
    modify_item = [numberOfFrames,totalDose]
    """
    try:
        if os.path.exists(out_json_file):
            with open(out_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tag0_start = data.get("tag0_start")
                tag0_length = data.get("tag0_length")
        with open(file_path, 'rb') as f:
            f.seek(tag0_start)
            XML_decode = f.read(tag0_length).decode('latin-1', errors='replace')
            
            match = re.search(
            r'<item name="commercialName">([^<]+)</item>',
            XML_decode
            ) #check camera type
            if match:
                if match.group(1) == "Falcon 4i":
                    print(match.group(1))
                    min_frame_time = 0.003275825
                elif match.group(1) == "Falcon 4":
                    print(match.group(1))
                    min_frame_time = 0.003275825
            
        # 替换exposureTime的值
        new_exposureTime = modify_item[0] * min_frame_time
        new_mean_dose = modify_item[1] / new_exposureTime
        modified = re.sub(
            r'(<item name="exposureTime" unit="s">)[\d.]+(</item>)',
            r'\g<1>{0}</item>'.format(new_exposureTime),
            XML_decode
        )
        
        # 替换meanDoseRate的值
        modified = re.sub(
            r'(<item name="meanDoseRate" unit="e/pixel/s">)[\d.]+(</item>)',
            r'\g<1>{0}</item>'.format(new_mean_dose),
            modified
        )
        # 替换numberOfFrames的值为新数值
        modified = re.sub(
            r'(<item name="numberOfFrames">)\d+(</item>)',
            r'\g<1>{0}</item>'.format(modify_item[0]),
            modified
        )
        # 替换totalDose的值
        modified = re.sub(
            r'(<item name="totalDose" unit="e/pixel">)[\d.]+(</item>)',
            r'\g<1>{0}</item>'.format(modify_item[1]),
            modified
        )

#        with open('XML-output', 'wb') as f:
#            f.write(modified.encode('latin-1', errors='replace'))
        
            
    except FileNotFoundError:
        print("错误：找不到文件 {}".format(file_path))
        return False,modify_item,1
    except Exception as e:
        print("处理文件时发生错误: {}".format(str(e)))
        return False,modify_item,1
    return True,modified.encode('latin-1', errors='replace'),len(modified)

def rewrite_65002(file_path,out_json_file,modify_item):
    """
    modify_item = [frameID,new_frameID]
    """
    try:
        if os.path.exists(out_json_file):
            with open(out_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tag_start = data.get("tag_start")
                tag_length = data.get("tag_length")
                
        with open(file_path, 'rb') as f:
            f.seek(tag_start[modify_item[0]])
            XML_decode = f.read(tag_length[modify_item[0]]).decode('latin-1', errors='replace')
            
            modified = re.sub(
                r'(<item name="frameID">)\d+(</item>)',
                r'\g<1>{0}</item>'.format(modify_item[1]),
                XML_decode
            )

    except FileNotFoundError:
        print("错误：找不到文件 {}".format(file_path))
        return False,modify_item,1
    except Exception as e:
        print("处理文件时发生错误: {}".format(str(e)))
        return False,modify_item,1
    return True,modified.encode('latin-1', errors='replace'),len(modified)
    
def separate_frame(out_json_file,required_length,threshold=0.0001):
    try:
        if os.path.exists(out_json_file):
            with open(out_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dose = data.get("dose")
        #check blank frame exist        
        has_above = any(num > threshold for num in dose)
        has_below_or_equal = any(num <= threshold for num in dose)
        has_both_categories = has_above and has_below_or_equal
        if not has_both_categories:
            return False
        
        #separate data frame region
        original_intervals = []
        in_interval = False
        current_start = 0
        
        for i, num in enumerate(dose):
            if num > threshold:
                if not in_interval:
                    current_start = i
                    in_interval = True
            else:
                if in_interval:
                    original_intervals.append((current_start, i - 1))
                    in_interval = False
                    
        if in_interval:
            original_intervals.append((current_start, len(dose) - 1))
            
            
        #adjust data frame region to equal number
        candidate_intervals = []
        
        for s, e in original_intervals:
            original_length = e - s + 1  # 原始区间长度
            
            if original_length == required_length:
                # 长度符合要求，直接添加
                candidate_intervals.append((s, e, sum(dose[s:e+1])))
            
            elif original_length > required_length:
                # 长度过长，缩小区间：寻找总和最大的连续子区间
                max_sum = -float('inf')
                best_window = (s, s + required_length - 1)
                
                # 滑动窗口计算最大和子区间
                for i in range(original_length - required_length + 1):
                    window_start = s + i
                    window_end = window_start + required_length - 1
                    window_sum = sum(dose[window_start:window_end+1])
                    
                    if window_sum > max_sum:
                        max_sum = window_sum
                        best_window = (window_start, window_end)
                
                candidate_intervals.append((best_window[0], best_window[1], max_sum))
            
            else:  # original_length < required_length
                # 检查是否有足够空间扩展到要求长度
                available_space = s + (len(dose) - 1 - e)  # 左侧+右侧可用空间
                needed_expansion = required_length - original_length
                
                if available_space < needed_expansion:
                    # 没有足够空间，跳过该区间
                    continue
                
                # 有足够空间，扩展区间（保证总和最大）
                possible_windows = []
                
                # 遍历所有可能的左右扩展组合
                for left_expand in range(0, min(needed_expansion, s) + 1):
                    right_expand = needed_expansion - left_expand
                    if right_expand < 0 or right_expand > (len(dose) - 1 - e):
                        continue
                    
                    window_start = s - left_expand
                    window_end = e + right_expand
                    window_sum = sum(dose[window_start:window_end+1])
                    possible_windows.append((window_sum, window_start, window_end))
                
                # 选择总和最大的窗口
                possible_windows.sort(reverse=True, key=lambda x: x[0])
                best_sum, best_start, best_end = possible_windows[0]
                candidate_intervals.append((best_start, best_end, best_sum))
                
        #remove overlap
        if not candidate_intervals:
            return True, [], []
        
        # 按区间起始位置排序
        candidate_intervals.sort(key=lambda x: x[0])
        non_overlapping = []
        last_end = -1
        
        for s, e, _ in candidate_intervals:
            # 检查当前区间是否与上一个区间重叠
            if s > last_end:
                non_overlapping.append((s, e))
                last_end = e
        
        # 提取最终的起始和结束位置列表
        starts = [s for s, e in non_overlapping]
        ends = [e for s, e in non_overlapping]
                
        json_arrays = [
            ("starts", starts),
            ("ends", ends),
        ]
        path = out_json_file + '_dose_sep'
        array_to_json(json_arrays,path)
        
    except FileNotFoundError:
        print("错误：找不到文件 {}".format(out_json_file))
        return False
    except Exception as e:
        print("处理文件时发生错误: {}".format(str(e)))
        return False
    return True

def separate_frame_inter(out_json_file,dose,required_length,threshold, first_range, blank_range,end_range,initial_blank, min_sep):
    try:

        #check blank frame exist        
        has_above = any(num > threshold for num in dose)
        has_below_or_equal = any(num <= threshold for num in dose)
        has_both_categories = has_above and has_below_or_equal
        if not has_both_categories:
            print("Error:no separation detected-1")
            return False,[],[]

        #separate data frame region
        original_intervals = []
        in_interval = False
        current_start = 0
        
        for i, num in enumerate(dose):
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
            
            
        #adjust data frame region to equal number
        candidate_intervals = []
        
        for s, e in original_intervals:
            
            original_length = e - s + 1  # 原始区间长度
            
            if original_length < min_sep:
                continue
            
            if original_length == required_length:
                # 长度符合要求，直接添加
                candidate_intervals.append((s, e, sum(dose[s:e+1])))
            
            elif original_length > required_length:
                # 长度过长，缩小区间：寻找总和最大的连续子区间
                max_sum = -float('inf')
                best_window = (s, s + required_length - 1)
                
                # 滑动窗口计算最大和子区间
                for i in range(original_length - required_length + 1):
                    window_start = s + i
                    window_end = window_start + required_length - 1
                    window_sum = sum(dose[window_start:window_end+1])
                    
                    if window_sum > max_sum:
                        max_sum = window_sum
                        best_window = (window_start, window_end)
                
                candidate_intervals.append((best_window[0], best_window[1], max_sum))
            
            else:  # original_length < required_length
                # 检查是否有足够空间扩展到要求长度
                available_space = s + (len(dose) - 1 - e)  # 左侧+右侧可用空间
                needed_expansion = required_length - original_length
                
                if available_space < needed_expansion:
                    # 没有足够空间，跳过该区间
                    continue
                
                # 有足够空间，扩展区间（保证总和最大）
                possible_windows = []
                
                # 遍历所有可能的左右扩展组合
                for left_expand in range(0, min(needed_expansion, s) + 1):
                    right_expand = needed_expansion - left_expand
                    if right_expand < 0 or right_expand > (len(dose) - 1 - e):
                        continue
                    
                    window_start = s - left_expand
                    window_end = e + right_expand
                    window_sum = sum(dose[window_start:window_end+1])
                    possible_windows.append((window_sum, window_start, window_end))
                
                # 选择总和最大的窗口
                possible_windows.sort(reverse=True, key=lambda x: x[0])
                best_sum, best_start, best_end = possible_windows[0]
                candidate_intervals.append((best_start, best_end, best_sum))
                
        #remove overlap
        if not candidate_intervals:
            print("Error:no separation detected-2")
            return False,[],[]
        
        # 按区间起始位置排序
        candidate_intervals.sort(key=lambda x: x[0])
        non_overlapping = []
        last_end = -1
        
        for s, e, _ in candidate_intervals:
            # 检查当前区间是否与上一个区间重叠
            if s > last_end:
                non_overlapping.append((s, e))
                last_end = e
        
        #check first separation
        after_first = process_first_interval(non_overlapping, dose, required_length, first_range, blank_range)

        
        #check blank gap
        after_check_gap = process_blank(after_first, dose, required_length, blank_range)
        
        #check end
        final_intervals = process_end(after_check_gap, dose, required_length, blank_range,end_range)

        
        # 提取最终的起始和结束位置列表
        starts = [s for s, e in final_intervals]
        ends = [e for s, e in final_intervals]
                
        json_arrays = [
            ("starts", starts),
            ("ends", ends),
        ]
        path = out_json_file + '_dose_sep'
        array_to_json(json_arrays,path)
        
    except Exception as e:
        print("处理文件时发生错误: {}".format(str(e)))
        return False,[],[]
    return True,starts,ends

def process_first_interval(non_overlapping, dose, required_length, first_range, blank_range):
    
    if not non_overlapping:
        return non_overlapping
    
    a_min, a_max = first_range
    b_min, b_max = blank_range
    A = non_overlapping[0]
    
    if A[0] <= a_min + required_length + b_min:
        
        return non_overlapping.copy()
    
    s_max = min(a_max, A[0] - required_length - b_min)
    
    
    B = find_max(dose,a_min,s_max,required_length)
    
    check_gap_result = check_gap(B,A,b_min)
    
    if check_gap_result:
        new_intervals = non_overlapping.copy()
        new_intervals.append(B)
        new_intervals.sort(key=lambda x: x[0])
        return new_intervals
    else:
        return non_overlapping.copy()
    
def process_end(after_check_gap, dose, required_length, blank_range,end_range):
    if not after_check_gap:
        return after_check_gap.copy()
        
    new_intervals = after_check_gap.copy()
    b_min, b_max = blank_range
    e_min, e_max = end_range
    
    E = after_check_gap[len(after_check_gap)-1]
    end_gap = len(dose) - E[1]
    if end_gap < e_min + required_length + b_min:
        return after_check_gap.copy()
    
    end_interval = (len(dose) - e_min, len(dose))
    new_intervals = generate_interval_by_gap(dose,new_intervals,required_length,E,end_interval,b_min,b_max)
    
    return new_intervals
    
   
def find_max(dose,s_min,s_max,required_length):
    max_sum = 0
    best_s = s_min
    
    for s in range(s_min,s_max + 1):
        e = s + required_length - 1
        current_sum = sum(dose[s:e + 1])
        if current_sum > max_sum:
            max_sum = current_sum
            best_s = s
    print("find_max", (best_s, best_s + required_length - 1))
    return (best_s, best_s + required_length - 1)


def process_blank(after_first, dose, required_length, blank_range):
    if not after_first:
        return after_first.copy()
    
    new_intervals = after_first.copy()
    b_min, b_max = blank_range
    i = 0
    while i < len(after_first) - 1 :
        check_gap_result = check_gap_add(after_first[i],after_first[i+1],b_min,required_length)
        
        if check_gap_result:
            new_intervals = generate_interval_by_gap(dose,new_intervals,required_length,after_first[i],after_first[i+1],b_min,b_max)
        else:
            print("process_blank",i,check_gap_result)
        i += 1
        
    new_intervals.sort(key=lambda x: x[0])
    return new_intervals


def check_gap(interval1,interval2,b_min):
    C_end = interval1[1]
    D_start = interval2[0]
    gap = D_start - C_end - 1
    
    
    if b_min <= gap:
        return True
    else:
        return False
    
def check_gap_add(interval1,interval2,b_min,required_length):
    C_end = interval1[1]
    D_start = interval2[0]
    gap = D_start - C_end
    
    s_min = b_min + required_length + b_min
    #print(s_min,gap)
    
    if s_min <= gap:
        return True
    else:
        return False
        
def generate_interval_by_gap(dose,after_first,required_length,interval1,interval2,b_min,b_max):
    new_intervals = after_first.copy()
    
    s_min = interval1[1] + b_min
    s_max = min(interval1[1] + b_max , interval2[0] - b_min - required_length )
    
    B = find_max(dose,s_min,s_max,required_length)
    check_gap_result = check_gap(B,interval2,b_min)
    if check_gap_result:
        new_intervals.append(B)
        
        while check_gap_add(B,interval2,b_min,required_length):
            s_min = B[1] + b_min
            s_max = min(B[1] + b_max , interval2[0] - b_min - required_length )
            B = find_max(dose,s_min,s_max,required_length)
            check_gap_result = check_gap(B,interval2,b_min)
            if check_gap_result:
                new_intervals.append(B)
                
        
    new_intervals.sort(key=lambda x: x[0])
    return new_intervals

def rewrite_eer(file_path,out_json_file,required_length,sep_frame_num,threshold, first_range, blank_range,end_range,initial_blank, min_sep):

    try:
        
        frame_start = []
        data_start = []
        data_length = []
        tag_start = []
        tag_length = []
        dose = []
        insert_str = []

        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f_in:
            #check header
            header = f_in.read(8)
            if len(header) < 8:
                print("Error: header too short!")
                return False
            byte_order = header[0:2]
            if byte_order == b'II':
                format_char = '<'  # 小端Intel
            elif byte_order == b'MM':
                format_char = '>'  # 大端Motorola
            else:
                print("Error: byte order not right!")
                return False
            version = struct.unpack(format_char + "H", header[2:4])[0]
            if version == 43:
                offset = struct.unpack(format_char + "H", header[4:6])[0]
            else:
                print("Error: not EER format!")
                return False
            
            #read frame starts
            while offset < file_size:
                f_in.seek(offset)
                oneframe_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                if oneframe_start == 0:
                    break
                frame_start.append(oneframe_start)
                f_in.seek(oneframe_start)
                entry_num = struct.unpack(format_char + "Q", f_in.read(8))[0]
                
                f_in.seek(oneframe_start+100) #tag4 dsata_start, 8+20*4+12=100
                onedata_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                data_start.append(onedata_start)
                
                f_in.seek(oneframe_start+160) #tag7 dsata_length, 8+20*7+12=160
                onedata_length = struct.unpack(format_char + "Q", f_in.read(8))[0]
                data_length.append(onedata_length)
                
                if entry_num == 9:
                    f_in.seek(oneframe_start+172) #tag8 tag_length, 8+20*8+4
                    onetag_length = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    tag_length.append(onetag_length)
                    
                    f_in.seek(oneframe_start+180) #tag8 tag_start, 8+20*8+12
                    onetag_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    tag_start.append(onetag_start)
                    
                    offset = oneframe_start+188 #next frame_start, 8+20*9
                elif entry_num == 10:
                    f_in.seek(oneframe_start+172) #tag8 tag0_length, 8+20*8+4
                    tag0_length = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    
                    f_in.seek(oneframe_start+180) #tag8 tag0_start, 8+20*8+12
                    tag0_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    
                    f_in.seek(oneframe_start+192) #tag9 tag_length, 8+20*9+4
                    onetag_length = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    tag_length.append(onetag_length)
                    
                    f_in.seek(oneframe_start+200) #tag9 tag_start, 8+20*9+12
                    onetag_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    tag_start.append(onetag_start)
                    
                    offset = oneframe_start+208 #next frame_start, 8+20*10
                    
                f_in.seek(onetag_start)  #read dose of each frame from tag of XML format
                XML_decode = f_in.read(onetag_length).decode('latin-1', errors='replace')
                XML_match = re.search(r'<item name="dose" unit="e/pixel">([\d.]+)</item>',XML_decode)
                if XML_match:
                    dose.append(float(XML_match.group(1)))
            
            
            #save all frame start info in out_json_file
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
            array_to_json(json_arrays,out_json_file) 
            
            #check if frame start info is currect
            f_in.seek(tag0_start)
            XML_decode = f_in.read(tag0_length).decode('latin-1', errors='replace')
            XML_match = re.search(r'<item name="numberOfFrames">(\d+)</item>',XML_decode)
            if XML_match:
                frame_num = XML_match.group(1)
                if int(frame_num) > len(dose):
                    return False
            
            #separate real frames from blank frames
            sep_check,frame_range_start,frame_range_end = separate_frame_inter(out_json_file,dose,required_length,threshold, first_range, blank_range,end_range,initial_blank, min_sep)
            if sep_check:
                
                print("frame_num: {0} end_gap: {1}".format(len(dose), len(dose) - frame_range_end[len(frame_range_end)-1]))
                if len(frame_range_start) != len(frame_range_end):
                    print("Error in frame separation: starts != ends")
                    return False
                #check frame separation
                if sep_frame_num > len(frame_range_start):
                    print("Error in frame separation: output frame number less than input!")
                    return False
                elif sep_frame_num < len(frame_range_start):
                    print("Error in frame separation: output frame number more than input!")
                    return False
            else:
                return False
            
            #get min_frame_time by check camera type
            f_in.seek(tag0_start)
            XML65001_decode = f_in.read(tag0_length).decode('latin-1', errors='replace')
            match = re.search(
            r'<item name="commercialName">([^<]+)</item>',
            XML65001_decode
            ) 
            #check camera type
            if match:
                if match.group(1) == "Falcon 4i":
                    print(match.group(1))
                    min_frame_time = 0.003275825
                elif match.group(1) == "Falcon 4":
                    print(match.group(1))
                    min_frame_time = 0.004212476
            else:
                return False

            
            for each_frame_range in range(sep_frame_num):
                new_frameID = required_length - 1
                
                new_data_start = [0] * required_length
                new_data_len = [0] * required_length
                new_tag_start = [0] * required_length
                new_tag_len = [0] * required_length
                dose_total = 0
                
                data_tag_len_total = 16
                
                add_end = file_path[:-4]  # 从末尾去掉4个字符（.eer）
                new_path = "{}_{i1}.eer".format(add_end,i1="{0:02d}".format(each_frame_range))
                
                #ori_log_path = os.path.join(os.path.dirname(file_path),"tomo_log.txt")
                ori_log_path = "{}_log".format(file_path)
                new_log_path = "{}log_sep.txt".format(add_end)
                
                insert_str.append(os.path.basename(new_path))
                temp_file = new_path + ".tmp"
                
                with open(temp_file, 'wb') as f_out:
                    
                    for each_frame in range(frame_range_end[each_frame_range],frame_range_start[each_frame_range]-1,-1):
                        #write tag 65002 of current frame
                        f_in.seek(tag_start[each_frame])
                        XML_decode = f_in.read(tag_length[each_frame]).decode('latin-1', errors='replace')
                        modified = re.sub(
                            r'(<item name="frameID">)\d+(</item>)',
                            r'\g<1>{0}</item>'.format(new_frameID),
                            XML_decode
                        )
                        
                        tag_65002 = modified.encode('latin-1', errors='replace')
                        f_out.write(tag_65002)
                        new_tag_start[new_frameID] = data_tag_len_total
                        new_tag_len[new_frameID] = len(tag_65002)
                        data_tag_len_total += new_tag_len[new_frameID]
                          
                        #write empty bit gap to separate tag and data
                        f_out.write(b'\x00')
                        data_tag_len_total += 1
                        
                        #write data of current frame
                        f_in.seek(data_start[each_frame])
                        f_out.write(f_in.read(data_length[each_frame]))
                        new_data_start[new_frameID] = data_tag_len_total
                        new_data_len[new_frameID] = data_length[each_frame]
                        data_tag_len_total += new_data_len[new_frameID]
                        
                        #cumulate dose_total for tag 65001
                        dose_total += dose[each_frame]
                        
                        new_frameID -= 1
                    
                    #write tag 65001
                    new_exposureTime = required_length * min_frame_time
                    new_mean_dose = dose_total / new_exposureTime
                    # updat exposureTime
                    modified = re.sub(
                        r'(<item name="exposureTime" unit="s">)[\d.]+(</item>)',
                        r'\g<1>{0}</item>'.format(new_exposureTime),
                        XML65001_decode
                    )
                    # update meanDoseRate
                    modified = re.sub(
                        r'(<item name="meanDoseRate" unit="e/pixel/s">)[\d.]+(</item>)',
                        r'\g<1>{0}</item>'.format(new_mean_dose),
                        modified
                    )
                    # update numberOfFrames
                    modified = re.sub(
                        r'(<item name="numberOfFrames">)\d+(</item>)',
                        r'\g<1>{0}</item>'.format(required_length),
                        modified
                    )
                    #print(modified)
                    #update totalDose
                    modified = re.sub(
                        r'(<item name="totalDose" unit="e/pixel">)[\d.]+(</item>)',
                        r'\g<1>{0}</item>'.format(dose_total),
                        modified
                    )
                    tag_65001 = modified.encode('latin-1', errors='replace')
                    f_out.write(tag_65001)
                    new_tag0_start = data_tag_len_total
                    new_tag0_len = len(tag_65001)
                    data_tag_len_total += new_tag0_len
                    
                    #write empty bit gap to separate tag and data
                    f_out.write(b'\x00')
                    data_tag_len_total += 1
                    
                    #write tag 10
                    first_frame_start = data_tag_len_total
                    
                    f_out.write(tag10(0))
                    f_out.write(struct.pack('Q', new_data_start[0]))
                    f_out.write(tag10(1))
                    f_out.write(struct.pack('Q', new_data_len[0]))
                    f_out.write(tag10(2))
                    f_out.write(struct.pack('Q', new_tag0_len))
                    f_out.write(struct.pack('Q', new_tag0_start))
                    f_out.write(tag10(3))
                    f_out.write(struct.pack('Q', new_tag_len[0]))
                    f_out.write(struct.pack('Q', new_tag_start[0]))
                    data_tag_len_total += 208
                    
                    #write tag 9
                    for rest_frame in range(1,required_length):
                        data_tag_len_total += 8
                        f_out.write(struct.pack('Q', data_tag_len_total))
                        f_out.write(tag9(0))
                        f_out.write(struct.pack('Q', new_data_start[rest_frame]))
                        f_out.write(tag9(1))
                        f_out.write(struct.pack('Q', new_data_len[rest_frame]))
                        
                        f_out.write(tag9(2))
                        f_out.write(struct.pack('Q', new_tag_len[rest_frame]))
                        f_out.write(struct.pack('Q', new_tag_start[rest_frame]))
                        data_tag_len_total += 188
                    
                    #write end tag
                    end_tag = 0
                    f_out.write(struct.pack('Q', end_tag))
                    data_tag_len_total += 8
                
                file_size = os.path.getsize(temp_file)
                size_check = data_tag_len_total - file_size
                if size_check != 16:
                    print("output file size not right!")
                    return False
                #print(temp_file,new_path)
                with open(temp_file, 'rb') as f_in2, open(new_path, 'wb') as f_out2:
                    #write header
                    f_out2.write(b'II+\x00\x08\x00\x00\x00')
                    #write first_frame_start
                    f_out2.write(struct.pack('Q', first_frame_start))
                    #write tag65002, data, tag65001, tag10, tag9, end tag
                    f_out2.write(f_in2.read(file_size))
                
                   
                #remove temp_file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        if not add_new_log_file(ori_log_path,new_log_path,insert_str):
            return False
            
    except FileNotFoundError:
        print("Error: {} not found".format(file_path))
        return False
    except Exception as e:
        print("Error: {}".format(str(e)))
        return False
    return True

def add_new_log_file(file_a, file_b, insert_str):
    try:
        # 读取文件A的内容
        with open(file_a, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        result_lines = []
        i = 0
        for line in lines:
            # 去除行首尾的空白字符（不影响中间的分割）
            stripped_line = line.strip()
            if not stripped_line:  # 处理空行
                result_lines.append(line)  # 保留原空行（包括换行符）
                continue
            
            # 按空格分割，连续空格视为一个分隔符，得到元素列表
            elements = stripped_line.split()
            
            # 根据元素数量处理
            if len(elements) >= 2:
                # 在第一和第二个元素之间插入指定内容
                new_elements = [elements[0]] + [insert_str[i]] + elements[1:]
                i += 1
            elif len(elements) == 1:
                # 只有一个元素时，在其后面添加插入内容
                print("Error: only one elements")
                return False
            else:
                # 空行已在前面处理，这里理论上不会触发
                new_elements = []
                return False
            
            # 将处理后的元素用空格连接，恢复为一行
            new_line = ' '.join(new_elements) + '\n'  # 补充换行符
            result_lines.append(new_line)
        
        # 写入文件B
        with open(file_b, 'w', encoding='utf-8') as f:
            f.writelines(result_lines)
        
        
    except FileNotFoundError as e:
        print("Error: {} not found".format(e.filename))
    except Exception as e:
        print("Error: {}".format(str(e)))
    return True

def tag10(clip_num):
    tag10_clip = []
    tag10_clip.append(b'\n\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x01\x01\x04\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x03\x01\x03\x00\x01\x00\x00\x00\x00\x00\x00\x00\xe9\xfd\x00\x00\x00\x00\x00\x00\x06\x01\x03\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x11\x01\x10\x00\x01\x00\x00\x00\x00\x00\x00\x00')
    tag10_clip.append(b'\x12\x01\x03\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x16\x01\x04\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x17\x01\x10\x00\x01\x00\x00\x00\x00\x00\x00\x00')
    tag10_clip.append(b'\xe9\xfd\x07\x00')
    tag10_clip.append(b'\xea\xfd\x07\x00')
    
    return tag10_clip[clip_num]

def tag9(clip_num):
    tag9_clip = []
    tag9_clip.append(b'\t\x00\x00\x00\x00\x00\x00\x00\x00\x01\x04\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x01\x01\x04\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x03\x01\x03\x00\x01\x00\x00\x00\x00\x00\x00\x00\xe9\xfd\x00\x00\x00\x00\x00\x00\x06\x01\x03\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x11\x01\x10\x00\x01\x00\x00\x00\x00\x00\x00\x00')
    tag9_clip.append(b'\x12\x01\x03\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x16\x01\x04\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x17\x01\x10\x00\x01\x00\x00\x00\x00\x00\x00\x00')
    tag9_clip.append(b'\xea\xfd\x07\x00')
    
    return tag9_clip[clip_num]


def out_json_path(file_path):
    if file_path.lower().endswith(".eer"):
        new_path = file_path[:-4]  # 从末尾去掉4个字符（.eer）
    else:
        new_path = file_path  # 如果没有.eer扩展名，保持原样

    # 加上_json
    new_path += "_json"
    return new_path

def process_eer_files(input_folder,output_folder,frame_num,threshold, first_range, blank_range,end_range,initial_blank, min_sep):
    if not os.path.isdir(input_folder):
        print("Error: folder '{}' not exist!".format(input_folder))
        return
    
    try:

        eer_files = []
        for root, dirs, files in os.walk(input_folder):
            for filename in files:
                if filename.endswith(".eer_log"):
                    log_path = os.path.join(root, filename)
                    with open(log_path, "r", encoding = "utf-8") as f:
                        lines = f.readlines()
                        eer_num = len(lines)
                    file = filename[:-len(".eer_log")] + ".eer"
                    print(" {} : processing...".format(file))
                    out_json_file = out_json_path(file)
                    out_json_name = os.path.join(output_folder, out_json_file)
                    file_path = os.path.join(root, file)
                    Fast_file_path = os.path.join(root, filename)
                    if rewrite_eer(file_path,out_json_name,int(frame_num),int(eer_num),float(threshold), first_range, blank_range,end_range,initial_blank, min_sep):
                        os.remove(file_path)
                        os.remove(Fast_file_path)
                        print(" {} : done!".format(file))
                    else:
                        new_file = str("failed_" + filename[:-len(".eer_log")]+ ".eer")
                        new_file_path = os.path.join(root,new_file)
                        os.rename(file_path,new_file_path)
                        
                    eer_files.append(file)
                    
        if not eer_files:
            print(" No eer file in '{}'".format(input_folder))
            return
        
        print(" {}  eer files, processed".format(len(eer_files)))
    except Exception as e:
        print("Error: {}".format(str(e)))
    return

def auto_process_eer_files(input_folder,output_folder,frame_num,threshold, first_range, blank_range,end_range,initial_blank, min_sep):
    if not os.path.isdir(input_folder):
        print("Error: folder '{}' not exist!".format(input_folder))
        return
    
    try:

        eer_files = []
        for root, dirs, files in os.walk(input_folder):
            for filename in files:
                if filename.endswith("log_sep.txt"):
                    log_path = os.path.join(root, filename)
                    with open(log_path, "r", encoding = "utf-8") as f:
                        lines = f.readlines()
                        eer_num = len(lines)
#                        print(eer_num,lines)

                        for i in range(eer_num):
                            
                            stripped_line = lines[i].strip()
                            elements = stripped_line.split()
                            if len(elements) >= 4:
                                current_lable = elements[4]
                            else:
                                current_lable = 0
                            tiltangle = round(float(elements[0]))
                            file_num_add = 1000 + tiltangle + 90
                        
                            file_eer = filename[:-len("log_sep.txt")] + "_" + "{0:02d}.eer".format(i)
                            file_eer_path = os.path.join(root, file_eer)
                            file_mrc = file_eer[:-len(".eer")] + ".mrc"
                            file_mrc_path = os.path.join(root, file_mrc)
                            file_mrc_tmp = file_eer[:-len(".eer")] + "tmp.mrc"
                            file_mrc_tmp_path = os.path.join(root, file_mrc_tmp)
                            file_jpg = "Nav_lable_" + str(current_lable) + "_" + str(file_num_add) + "_" + str(tiltangle) + "_" + file_eer + ".mrc"
                            file_jpg_path = os.path.join("/mnt/user_data", os.path.basename(root), file_jpg)
                            check_frame_num, read_from_frame_num = read_frame_num(file_eer_path)
                            if check_frame_num:
                                if read_from_frame_num == frame_num:
                                    if not os.path.exists(file_jpg_path):
                                        os.system("MotionCor2 -InEer {} -EerSampling 8 -OutMrc {} -Group 20 -Gpu 0,1,2,3".format(file_eer_path,file_mrc_path))
                                        os.system("clip flipy {} {}".format(file_mrc_path,file_jpg_path))
                                        #os.system("mrc2tif -C 0,255 {} {}".format(file_mrc_tmp_path,file_jpg_path))
                                        os.remove(file_mrc_path)
                                        #os.remove(file_mrc_tmp_path)
                                        #print("do motion correction here!")
                if filename.endswith(".eer_log"):
                    log_path = os.path.join(root, filename)
                    with open(log_path, "r", encoding = "utf-8") as f:
                        lines = f.readlines()
                        eer_num = len(lines)
                    file = filename[:-len(".eer_log")] + ".eer"
                    print(" {} : processing...".format(file))
                    out_json_file = out_json_path(file)
                    out_json_name = os.path.join(output_folder, out_json_file)
                    file_path = os.path.join(root, file)
                    Fast_file_path = os.path.join(root, filename)
                    if os.path.exists(file_path):
                        if rewrite_eer(file_path,out_json_name,int(frame_num),int(eer_num),float(threshold), first_range, blank_range,end_range,initial_blank, min_sep):
                            os.remove(file_path)
                            os.remove(Fast_file_path)
                            print(" {} : done!".format(file))
                        else:
                            new_file = str("failed_" + filename[:-len(".eer_log")]+ ".eer")
                            new_file_path = os.path.join(root,new_file)
                            os.rename(file_path,new_file_path)
                        
                        eer_files.append(file)
                    
        if not eer_files:
            print(" No eer file in '{}'".format(input_folder))
            return
        
        print(" {}  eer files, processed".format(len(eer_files)))
    except Exception as e:
        print("Error: {}".format(str(e)))
    return
   
def read_end_gap(out_json_file):
    try:
        if os.path.exists(out_json_file):
            with open(out_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dose = data.get("dose")
        path = out_json_file + '_dose_sep'
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                end = data.get("ends")
        print("frame_num: {0}; end_gap: {1}".format(len(dose), len(dose) - end[len(end)-1] ))
    except FileNotFoundError:
        print("错误：找不到文件 {}".format(out_json_file))
        return False
    except Exception as e:
        print("处理文件时发生错误: {}".format(str(e)))
        return False
    return True

def show_separate_info(file_path,out_json_file,required_length,sep_frame_num,threshold, first_range, blank_range,end_range,initial_blank, min_sep):
    try:
        
        frame_start = []
        data_start = []
        data_length = []
        tag_start = []
        tag_length = []
        dose = []

        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f_in:
            #check header
            header = f_in.read(8)
            if len(header) < 8:
                print("Error: header too short!")
                return False
            byte_order = header[0:2]
            if byte_order == b'II':
                format_char = '<'  # 小端Intel
            elif byte_order == b'MM':
                format_char = '>'  # 大端Motorola
            else:
                print("Error: byte order not right!")
                return False
            version = struct.unpack(format_char + "H", header[2:4])[0]
            if version == 43:
                offset = struct.unpack(format_char + "H", header[4:6])[0]
            else:
                print("Error: not EER format!")
                return False
            
            #read frame starts
            while offset < file_size:
                f_in.seek(offset)
                oneframe_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                if oneframe_start == 0:
                    break
                frame_start.append(oneframe_start)
                f_in.seek(oneframe_start)
                entry_num = struct.unpack(format_char + "Q", f_in.read(8))[0]
                
                f_in.seek(oneframe_start+100) #tag4 dsata_start, 8+20*4+12=100
                onedata_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                data_start.append(onedata_start)
                
                f_in.seek(oneframe_start+160) #tag7 dsata_length, 8+20*7+12=160
                onedata_length = struct.unpack(format_char + "Q", f_in.read(8))[0]
                data_length.append(onedata_length)
                
                if entry_num == 9:
                    f_in.seek(oneframe_start+172) #tag8 tag_length, 8+20*8+4
                    onetag_length = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    tag_length.append(onetag_length)
                    
                    f_in.seek(oneframe_start+180) #tag8 tag_start, 8+20*8+12
                    onetag_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    tag_start.append(onetag_start)
                    
                    offset = oneframe_start+188 #next frame_start, 8+20*9
                elif entry_num == 10:
                    f_in.seek(oneframe_start+172) #tag8 tag0_length, 8+20*8+4
                    tag0_length = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    
                    f_in.seek(oneframe_start+180) #tag8 tag0_start, 8+20*8+12
                    tag0_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    
                    f_in.seek(oneframe_start+192) #tag9 tag_length, 8+20*9+4
                    onetag_length = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    tag_length.append(onetag_length)
                    
                    f_in.seek(oneframe_start+200) #tag9 tag_start, 8+20*9+12
                    onetag_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    tag_start.append(onetag_start)
                    
                    offset = oneframe_start+208 #next frame_start, 8+20*10
                    
                f_in.seek(onetag_start)  #read dose of each frame from tag of XML format
                XML_decode = f_in.read(onetag_length).decode('latin-1', errors='replace')
                XML_match = re.search(r'<item name="dose" unit="e/pixel">([\d.]+)</item>',XML_decode)
                if XML_match:
                    dose.append(float(XML_match.group(1)))
            
            
            #save all frame start info in out_json_file
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
            array_to_json(json_arrays,out_json_file) 
            
            #check if frame start info is currect
            f_in.seek(tag0_start)
            XML_decode = f_in.read(tag0_length).decode('latin-1', errors='replace')
            XML_match = re.search(r'<item name="numberOfFrames">(\d+)</item>',XML_decode)
            if XML_match:
                frame_num = XML_match.group(1)
                if int(frame_num) > len(dose):
                    return False
            
            #separate real frames from blank frames
            sep_check,frame_range_start,frame_range_end = separate_frame_inter(out_json_file,dose,required_length,threshold, first_range, blank_range,end_range,initial_blank, min_sep)
            if sep_check:
                
                print("frame_num: {0} end_gap: {1}".format(len(dose), len(dose) - frame_range_end[len(frame_range_end)-1]))
                if len(frame_range_start) != len(frame_range_end):
                    print("Error in frame separation: starts != ends")
                    return False
                #check frame separation
                if sep_frame_num > len(frame_range_start):
                    print("Error in frame separation: output frame number less than input!")
                    return False
                elif sep_frame_num < len(frame_range_start):
                    print("Error in frame separation: output frame number more than input!")
                    return False
            else:
                return False
    except FileNotFoundError:
        print("错误：找不到文件 {}".format(file_path))
        return False
    except Exception as e:
        print("处理文件时发生错误: {}".format(str(e)))
        return False
    return True

def read_frame_num(file_path):
    try:
        frame_num = 0
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f_in:
            #check header
            header = f_in.read(8)
            if len(header) < 8:
                print("Error: header too short!")
                return False, frame_num
            byte_order = header[0:2]
            if byte_order == b'II':
                format_char = '<'  # 小端Intel
            elif byte_order == b'MM':
                format_char = '>'  # 大端Motorola
            else:
                print("Error: byte order not right!")
                return False, frame_num
            version = struct.unpack(format_char + "H", header[2:4])[0]
            if version == 43:
                offset = struct.unpack(format_char + "H", header[4:6])[0]
            else:
                print("Error: not EER format!")
                return False, frame_num
            
            #read frame starts
            if offset < file_size:
                f_in.seek(offset)
                oneframe_start = struct.unpack(format_char + "Q", f_in.read(8))[0]
                if oneframe_start == 0:
                    return False, frame_num
                
                f_in.seek(oneframe_start)
                entry_num = struct.unpack(format_char + "Q", f_in.read(8))[0]
                if entry_num == 10:
                    f_in.seek(oneframe_start+172) #tag8 tag0_length, 8+20*8+4
                    tag0_length = struct.unpack(format_char + "Q", f_in.read(8))[0]
                    
                    f_in.seek(oneframe_start+180) #tag8 tag0_start, 8+20*8+12
                    tag0_start = struct.unpack(format_char + "Q", f_in.read(8))[0]

                                        
                    f_in.seek(tag0_start) 
                    XML_decode = f_in.read(tag0_length).decode('latin-1', errors='replace')
                    XML_match = re.search(r'<item name="numberOfFrames">(\d+)</item>',XML_decode)
                    if XML_match:
                        print(int(XML_match.group(1)))
                        frame_num = int(XML_match.group(1))
                        
                    else:
                        return False,frame_num
                else:
                    return False,frame_num
            else:
                    return False,frame_num
 
    except FileNotFoundError:
        print("Error {} no found".format(file_path))
        return False, frame_num
    except Exception as e:
        print("Error: {}".format(str(e)))
        return False,frame_num
    return True, frame_num

if __name__ == "__main__":
    #Falcon4i
    first_range = (480, 511)
    blank_range = (90, 110)
    end_range = (120, 145)
    #Falcon4
    #first_range = (83, 135)
    #blank_range = (40, 72)
    #end_range = (300, 400)
    
    #file_path = "Z:\\TemScripting\\BM-Falcon\\20251208_tomo_test_0.76s_error18\\Falcon4_00000.eer"
    #chenck, frame_num = read_frame_num(file_path)
    #print(frame_num)
    #out_json_file = out_json_path(file_path)
    
    parser = argparse.ArgumentParser(description='auto separate eer')
    parser.add_argument('frame_num', help='frame num of small eer')
    args = parser.parse_args()

    try:
        print(int(args.frame_num))
    except:
        print("frame_num should be integer.")
        sys.exit(1)

    folder = os.path.dirname(os.path.abspath(sys.argv[0]))
    run_sign = True
    if os.path.exists(os.path.join(folder,"stop.txt")):
        run_sign = False
    while run_sign:
        time.sleep(10)
        auto_process_eer_files(folder, folder, int(args.frame_num), 0.0001, first_range, blank_range,end_range,400,10)
        """
        # input: 
            (1) input folder, 
            (2) json file output folder, 
            (3) frame num for each eer file
            (4) separate threshold
            (5) first range from calculate_sep_range.py
            (6) blank_range from calculate_sep_range.py
            (7) end_range from calculate_sep_range.py
            (8) initail blank frame numb
            (9) min frame num for each separation file
        """

    
        
        
        
    
