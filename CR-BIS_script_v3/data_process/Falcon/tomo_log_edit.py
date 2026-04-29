import os,sys

def replace_lines_by_array(file_a_path, ARRAY_add, ARRAY_remove, file_b_path):
    print("1")
    # 验证参数有效性
    if not os.path.exists(file_a_path):
        raise FileNotFoundError("no {}".format(file_a_path))
    
    # 读取文件a的所有行
    with open(file_a_path, 'r', encoding='utf-8') as f_a:
        lines = f_a.readlines()
    
    # 处理每一行：匹配则替换为对应文件内容
    processed_lines = []
    for line in lines:
        replaced = False
        # 遍历数组b查找匹配
        for match_text, replace_file_path in ARRAY_add:
            if match_text in line:
                # 读取替换文件的内容（保留换行格式）
                with open(replace_file_path, 'r', encoding='utf-8') as f_replace:
                    replace_content = f_replace.read()
                # 将匹配行替换为替换文件内容（末尾补换行避免拼接问题）
                processed_lines.append(replace_content)
                replaced = True
                break  # 匹配到一个元素即停止，避免重复替换
        for match_text, replace_file_path in ARRAY_remove:
            if match_text in line:
                replaced = True
                break
        if not replaced:
            processed_lines.append(line)  # 未匹配的行保留原样
    
    
    with open(file_b_path, 'w', encoding='utf-8') as f_a:
        f_a.writelines(processed_lines)
    
    print("done!")
    return ''.join(processed_lines)

def insert_file_list(folder):
    ARRAY_add = []
    ARRAY_remove = []
    try:
        
        for root, dirs, files in os.walk(folder):
            for filename in files:
                if filename.endswith("log_sep.txt"):
                    ori_file_name = filename[:-len("log_sep.txt")] + ".eer"
                    new_file_path = os.path.join(root,filename)
                    ARRAY_add.append((ori_file_name,new_file_path))
                if filename.endswith(".eer_log"):
                    ori_file_name = filename[:-len(".eer_log")] + ".eer"
                    new_file_path = os.path.join(root,filename)
                    ARRAY_remove.append((ori_file_name,new_file_path))
                    print("{} separation failed!".format(filename[:-len(".eer_log")] + ".eer"))
                    
        
    except Exception as e:
        print("Error: {}".format(str(e)))
    return ARRAY_add, ARRAY_remove

if __name__ == "__main__":
    
    folder = os.path.dirname(os.path.abspath(sys.argv[0]))
    ARRAY_add, ARRAY_remove  = insert_file_list(folder)
     
    FILE_A = os.path.join(folder,"tomo_log.txt")
    FILE_B = os.path.join(folder,"tomo_log_new.txt")
    if os.path.exists(FILE_B):
        os.remove(FILE_B)
    replace_lines_by_array(FILE_A, ARRAY_add, ARRAY_remove,FILE_B)
    
    

