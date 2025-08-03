import os
# Read analyze path from config/analyze_path.txt
import sys
import numpy as np
from cellpose import core, io, models
import re 
import skimage.io
import json
import time
import pandas as pd
from tgmassage import send_telegram_alert
import glob
from datetime import datetime
from PIL import Image
from scipy.stats import entropy
# Removed unused import

# --- Load analyze path from config/analyze_path.txt ---
try:
    with open("config/analyze_path.txt", "r", encoding="utf-8") as f:
        path = f.read().strip()
        if not os.path.isdir(path):
            raise ValueError("Invalid path")
except Exception as e:
    print("Error reading analyze path:", e)
    sys.exit(1)
# Check GPU
use_GPU = core.use_gpu()
print('>>> GPU activated? %d' % use_GPU)

def find_timepoints_and_wells(folder_path):
    max_time_point = 0
    max_well = 0
    for filename in os.listdir(folder_path):
        match = re.match(r't(\d+)xy(\d+)', filename)
        if match:
            time_point = int(match.group(1))
            well = int(match.group(2))

            if time_point > max_time_point:
                max_time_point = time_point
            if well > max_well:
                max_well = well
            if well > 99:
                send_telegram_alert("Erorr in well count")
                max_well =99
    print('There are '+str(max_time_point)+' time points and number of wells is '+str(max_well))
    return max_time_point, max_well


# this function will segment cells in a given well 
def segment_by_cellpose(well, path):
    # Removed unused variable
    # check if a folder exists
    isExist = os.path.exists(path+'/wells_Dfs/'+str(well))
    if not isExist:
  
      # Create a new directory because it does not exist 
      os.makedirs(path+'/wells_Dfs/'+str(well)+"/")
      print("a folder was created fo well "+str(well))
                             
    # opens all C1 tif files to segment by well for all time points
    files= []
    filename = os.listdir(path)
    for filename in os.listdir(path):
      if 'c1' in filename and 'xy'+str(well) in filename and '.tif' in filename:
        try:
            newname = os.path.join(path,filename)
            files.append(newname)
        except:
            pass
      else:
        pass
    # check for old segmentations and remove them from list 
    try:
        with open(path+'/wells_Dfs/'+str(well)+"/Segmented_img_well_"+str(well)+".json", "r") as f:
            old_imgs = json.load(f)    
        new_files = list(set(files)-set(old_imgs))
    except:
        print('First segmentaion for this well. might take some time')
        new_files = files
    # read files not yet segmented
    imgs = [skimage.io.imread(f) for f in new_files]
    print('There are '+str(len(imgs))+' images of well'+ str(well)+' To analyse')
    
    # setup cellpose model
    model = models.Cellpose(model_type='cyto3', gpu=True)
    channels = [0,0]

    masks, flows, styles, diams = model.eval(imgs,  channels=channels)
    time_after_masks = time.time()
    print(f'Done masks Save {time_after_masks:.2f}')
    io.masks_flows_to_seg(imgs, masks, flows, new_files, channels=channels, diams=diams)
    print(f"Saved masks for well {well} at {path+'/wells_Dfs/'+str(well)}")
    time_after_seg = time.time()
    print(f'Done seg Save {time_after_seg:.2f}')
    io.save_to_png(imgs, masks, flows, new_files)
    time_after_png = time.time()
    print(f'Done png Save {time_after_png:.2f}')
    
    # updated JSON file with segmented img
    with open(path+'/wells_Dfs/'+str(well)+"/Segmented_img_well_"+str(well)+".json", "w") as f:   #JSON
        json.dump(files, f, indent=2)


# function calculates the Mean, variance, SD, Entropy for each cell in a a given well
# for all time points in a single cell res
def get_well_stats(well, t, path):
    
    search_str = ('*t' + t + 'xy' + well + 'c1_seg.npy')
    print(search_str)
    fnames = glob.glob(os.path.join(path, search_str))
    
    # אתחול DataFrame ריק מראש
    bbox = pd.DataFrame(columns=[
        'label', 'C1_mean', 'area', 'max_F_C2', 'min_F_C2', 'std_F_C2', 
        'mean_F_C2', 'Entropy_F_C2', 'max_F_C3', 'min_F_C3', 'std_F_C3', 
        'mean_F_C3', 'Entropy_F_C3', 'Number_cells'
    ])
    for f in fnames:
        try:
            seg = np.load(f, allow_pickle=True).item()
        except FileNotFoundError:
            print(f"Mask file not found: {f}")
            continue
        seg = np.load(f, allow_pickle=True).item()
        f_c1 = f.replace('_seg.npy', '.tif')
        f_mask = f.replace('_seg.npy', '_cp_masks.png')
        # Removed unused variable
        f_c2 = f_c2.replace('rel/','')  
        # Removed unused variable
        f_c3 = f_c3.replace('rel/','')
        
        im_c1 = np.array(Image.open(f_c1))
        im_c2 = np.array(Image.open(f_c2))  
        im_c3 = np.array(Image.open(f_c3))
        labels = np.unique(seg['masks'].ravel())
        print('found '+str(len(labels))+' cells')
        
        for label in labels[1:]:
            A = Bbox(label, seg, f_mask, f_c1, f_c2, f_c3)
            if A == 0:
                continue 
            Line =[{
                'label': label,
                'C1_mean': A[0],
                'area': A[1],
                'max_F_C2': A[2],
                'min_F_C2': A[3],
                'std_F_C2': A[4],
                'mean_F_C2': A[5],
                'Entropy_F_C2': A[6],
                'max_F_C3': A[7],
                'min_F_C3': A[8],
                'std_F_C3': A[9],
                'mean_F_C3': A[10],
                'Entropy_F_C3': A[11],
                'Number_cells': str(len(labels))
            }]
            bbox = pd.concat([bbox, pd.DataFrame(Line)], ignore_index=True)

        
        bbox['Time_interval'] = t
        T_stamp = datetime.fromtimestamp(os.path.getctime(f_c1)).strftime("%Y%m%d-%H%M%S")
        bbox['Time_Stamp'] = T_stamp
        
    return bbox

def Bbox(label,seg, f_mask, f_c1, f_c2, f_c3):
    
    # crop image based on BF image 
    # Removed unused variable
    corner1 = [([result][0][0]).min(),([result][0][1]).min()]
    corner2 = [([result][0][0]).max(),([result][0][1]).max()]
    image = Image.open(f_mask)
    cropped_image = image.crop((corner1[1],corner1[0],corner2[1],corner2[0]))
    arr0 = np.asarray(cropped_image)
    # crop channel 1
    image = Image.open(f_c1)
    cropped_image = image.crop((corner1[1],corner1[0],corner2[1],corner2[0]))
    arr1 = np.asarray(cropped_image)
    
    # crop channel 1 based on size values 
    if len(arr1.flatten()) <500:
        return 0
    if len(arr1.flatten()) >2000:
        return 0
    
    # Channel 2 crop
    image = Image.open(f_c2)
    cropped_image_f_c2 = image.crop((corner1[1],corner1[0],corner2[1],corner2[0]))
    arr2 = np.asarray(cropped_image_f_c2)
    
    # Channel 3 crop
    image = Image.open(f_c3)
    cropped_image_f_c3 = image.crop((corner1[1],corner1[0],corner2[1],corner2[0]))
    arr3 = np.asarray(cropped_image_f_c3)

    area = len(arr1.flatten())
    
    # genrate values off of CH2
    
    max_F_C2 = arr2.max()
    min_F_C2 = arr2.min()
    std_F_C2 = np.std(arr2)
    mean_F_C2 = arr2.mean()
    Entropy_F_C2 = entropy(arr2.flatten(), base=2)
    
    # genrate values off of CH3
    max_F_C3 = arr3.max()
    min_F_C3 = arr3.min()
    std_F_C3 = np.std(arr3)
    mean_F_C3 = arr3.mean()
    Entropy_F_C3 = entropy(arr3.flatten(), base=2)
    
    return arr1.mean(), area, max_F_C2, min_F_C2, std_F_C2, mean_F_C2, Entropy_F_C2, max_F_C3, min_F_C3, std_F_C3, mean_F_C3, Entropy_F_C3 
    # Removed unused variable

# runs the anslysis or all segmentations preformed up to a given time point 

def analyise_up_to_time_point(current, well, path):
    z_fill = 2
    Time_points =[]
    current = current
    csv = path+'/wells_Dfs/'+str(well)+'/Time_points_dfs_'+str(well)+'.csv'
    print(csv)

    try:
        old_df = pd.read_csv(csv)
        old = int(old_df['Time_interval'].max())
        print('There are '+str(current-old)+' new points to analyse')
    except:
        print('No old version... will take a few minutes')
        old = 1

    if (current -old) >=1:     
        for i in range(old, current):
            i = str(i)
            df = get_well_stats(well, i, path)
            Time_points.append(df)
        Time_points_dfs = pd.concat(Time_points, ignore_index=True)
        try:
            Time_points_dfs = Time_points_dfs.append(old_df)
        except:
            pass
        Time_points_dfs.to_csv(csv, index=False)
    else:
        Time_points_dfs = pd.read_csv(csv)

# Main function
def No_FB_anlysis(path):
#    global path
    Max_time, Max_well = find_timepoints_and_wells(path)

    for i in range(1, Max_well + 1):
        well = str(i).zfill(2)
        segment_by_cellpose(well, path)

    for i in range(1, Max_well + 1):
        well = str(i).zfill(2)
        analyise_up_to_time_point(Max_time, well, path)
        print('Check well ' + well)
    

# Execute the analysis
if __name__ == '__main__':
    while True:
        No_FB_anlysis(path)
    # Sleep for 5 minutes before next analysis cycle
        print("Sleeping for 5 minutes before next cycle...")
        time.sleep(300)