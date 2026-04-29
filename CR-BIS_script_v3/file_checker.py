#C:\Titan\OnSystemUI\virtualenv\Scripts\python.exe
import os, sys, time, math
import comtypes.client

def process_next_tilt_file(file_path):
    """check next_tilt.txt, read and delete file"""
    try:
        
        time.sleep(1)
        
        # read file
        with open(file_path, 'r') as file:
            content = file.read().strip()
        
        # split content
        numbers = [float(num) for num in content.split()]
        
        # check numbers
        if numbers:
            next_tilt_angle = numbers[0]
            next_Stage_X = numbers[1]
            next_Stage_Y = numbers[2]
            next_Stage_Z = numbers[3]
            print("NEXT tilt angle: {}, Stage: {},{},{}".format(next_tilt_angle,next_Stage_X,next_Stage_Y,next_Stage_Z))
            #tilt_stage_to(next_tilt_angle,next_Stage_X,next_Stage_Y,next_Stage_Z)
            tilt_stage_to_fast(next_tilt_angle,next_Stage_X,next_Stage_Y,next_Stage_Z)
        else:
            print("file empty!")
            
    except Exception as e:
        print("read error: {}".format(e))
        return
    
    try:
        # delete file
        os.remove(file_path)
        print("delete file")
    except OSError as e:
        print("delete failed: {}, error: {}".format(e.errno,e.strerror))
        
def tilt_stage_to(next_tilt_angle,next_Stage_X,next_Stage_Y,next_Stage_Z):
    try:
        my_tem = comtypes.client.CreateObject("TEMScripting.Instrument")
    except:
        return print("create TEMScripting.Instrument failed!")
    
    try:
        tem_stage = my_tem.Stage
    except:
        return print("create tem_stage failed!")
        
    try:
    	tem_position = tem_stage.Position
    except:
    	return print("create tem_position failed!")
    	

    current_A = math.degrees(tem_position.A)
    print("{},{}".format(current_A,math.radians(current_A)))
    current_X = tem_position.X * 1000000
    current_Y = tem_position.Y * 1000000
    current_Z = tem_position.Z * 1000000
    diff_A = next_tilt_angle - current_A
    diff_X = next_Stage_X - current_X
    diff_Y = next_Stage_Y - current_Y
    diff_Z = next_Stage_Z - current_Z
    
    if abs(diff_A) > 0.5:
        if diff_A > 0:
            try:
                # tiltup in step 6 degree
                while abs(current_A - next_tilt_angle) > 0.5:
                    remainder = next_tilt_angle - current_A
                    step = min(6, remainder)
                    current_A += step
                    tem_position.A = math.radians(current_A)
                    print("{}".format(current_A))
                    my_tem.Stage.GoTo(tem_position, 8)
                tem_position.A = math.radians(next_tilt_angle)
                print("{}".format(next_tilt_angle))
                my_tem.Stage.GoTo(tem_position, 8)
                #my_tem.Stage.GoTo(tem_position, 3)
            except:
                return print("stage moveto failed!")
        else:
            # tilt backlash 3 degree
            temp_A = next_tilt_angle - 3
            # tilt down in step 6 degree
            try:
                while abs(current_A - temp_A) > 0.5:
                    remainder = current_A - temp_A
                    step = min(6, remainder)
                    current_A -= step
                    tem_position.A = math.radians(current_A)
                    print("{}".format(current_A))
                    my_tem.Stage.GoTo(tem_position, 8)
            
                tem_position.A = math.radians(next_tilt_angle)
                print("{}".format(next_tilt_angle))
                my_tem.Stage.GoTo(tem_position, 8)
                #my_tem.Stage.GoTo(tem_position, 3)
            except:
                return print("stage moveto failed!")
    if abs(diff_X) > 0.5 or abs(diff_Y) > 0.5 or abs(diff_Z) > 0.5:
        try:
            # backlash 5 um
            tem_position.X = ( next_Stage_X + 5 ) * 0.000001
            tem_position.Y = ( next_Stage_Y + 5 ) * 0.000001
            tem_position.Z = next_Stage_Z * 0.000001
            my_tem.Stage.GoTo(tem_position, 7)
            tem_position.X = next_Stage_X * 0.000001
            tem_position.Y = next_Stage_Y * 0.000001
            my_tem.Stage.GoTo(tem_position, 3)
        except:
            return print("stage moveto failed!")

    return print("NEXT completed!")

def tilt_stage_to_fast(next_tilt_angle,next_Stage_X,next_Stage_Y,next_Stage_Z):
    try:
        my_tem = comtypes.client.CreateObject("TEMScripting.Instrument")
    except:
        return print("create TEMScripting.Instrument failed!")
    
    try:
        tem_stage = my_tem.Stage
    except:
        return print("create tem_stage failed!")
        
    try:
    	tem_position = tem_stage.Position
    except:
    	return print("create tem_position failed!")
    	

    current_A = math.degrees(tem_position.A)
    print("{},{}".format(current_A,math.radians(current_A)))
    current_X = tem_position.X * 1000000
    current_Y = tem_position.Y * 1000000
    current_Z = tem_position.Z * 1000000
    diff_A = next_tilt_angle - current_A
    diff_X = next_Stage_X - current_X
    diff_Y = next_Stage_Y - current_Y
    diff_Z = next_Stage_Z - current_Z
    
    if abs(diff_A) > 0.5:
        if diff_A < 0:
            # tilt backlash 3 degree
            temp_A = next_tilt_angle - 3
            # tilt down in step 6 degree
            try:
                tem_position.A = math.radians(temp_A)
                print("{}".format(temp_A))
                my_tem.Stage.GoTo(tem_position, 8)
            except:
                return print("stage moveto failed!")
        
        try:
            tem_position.A = math.radians(next_tilt_angle)
            print("{}".format(next_tilt_angle))
            my_tem.Stage.GoTo(tem_position, 8)
        except:
            return print("stage moveto failed!")
    if abs(diff_X) > 0.5 or abs(diff_Y) > 0.5 or abs(diff_Z) > 0.5:
        try:
            # backlash 5 um
            tem_position.X = ( next_Stage_X + 5 ) * 0.000001
            tem_position.Y = ( next_Stage_Y + 5 ) * 0.000001
            tem_position.Z = next_Stage_Z * 0.000001
            my_tem.Stage.GoTo(tem_position, 7)
            tem_position.X = next_Stage_X * 0.000001
            tem_position.Y = next_Stage_Y * 0.000001
            my_tem.Stage.GoTo(tem_position, 3)
        except:
            return print("stage moveto failed!")

    return print("NEXT completed!")

def main():
    """main function:check next_tilt.txt"""
    # only check script fir
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    directory = script_dir
    file_name = "next_tilt.txt"
    file_path = os.path.join(directory, file_name)
    
    print("start checking: {}".format(directory))
    while True:
        # check file
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print("found: {}".format(file_path))
            process_next_tilt_file(file_path)
        else:
            print("NOT found: {}".format(file_path))
        
        # wait for 1 sec
        time.sleep(1)

if __name__ == "__main__":
    main()    
