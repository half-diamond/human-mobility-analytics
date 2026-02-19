import pandas as pd
import os
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import pyproj
import numpy as np
geod = pyproj.Geod(ellps='WGS84')

def to_datetime(string):
    return dt.datetime.strptime(string, '%Y-%m-%d %H:%M:%S')

def calculate_distance(long1, lat1, long2, lat2):
    if lat1 == lat2 and long1 == long2:
        return 0
    if False in np.isfinite([long1, long2, lat1, lat2]):
        return np.nan
    if lat1 < -90 or lat1 > 90 or lat2 < -90 or lat2 > 90:
        return np.nan
    if long1 < -180 or long1 > 180 or long2 < -180 or long2 > 180:
        return np.nan
    angle1,angle2,distance = geod.inv(long1, lat1, long2, lat2)
    return distance

def calculate_velocity(distance, timedelta):
    if timedelta.total_seconds() == 0: return np.nan
    return distance / timedelta.total_seconds()

def calculate_acceleration(velocity, velocity_next_position, timedelta):
    delta_v = velocity_next_position - velocity
    if timedelta.total_seconds() == 0: return np.nan
    return delta_v / timedelta.total_seconds()


headers_trajectory = ['lat', 'long', 'null', 'altitude','timestamp_float', 'date', 'time']

def load_trajectory_df(full_filename):
    # print("done")
    subfolder = full_filename.split('\\')[-3]
    trajectory_id = full_filename.split('\\')[-1].split('.')[0]
    
    df = pd.read_csv(full_filename, skiprows = 6, header = None, names = headers_trajectory)
   
    df['datetime'] = df.apply(lambda z: to_datetime(z.date + ' ' + z.time), axis=1)
    df['datetime_next_position'] = df['datetime'].shift(-1)
    df['timedelta'] = df.apply(lambda z: z.datetime_next_position - z.datetime, axis=1)
    df = df.drop(['datetime_next_position'], axis=1)
    df = df.drop(['null', 'timestamp_float', 'date', 'time'], axis=1)
    
    
    df['long_next_position'] = df['long'].shift(-1)
    df['lat_next_position'] = df['lat'].shift(-1)
    df['distance'] = df.apply(lambda z: calculate_distance(z.long, z.lat, z.long_next_position, z.lat_next_position), axis=1)
    df = df.drop(['long_next_position', 'lat_next_position'], axis=1)
    
    df['velocity'] = df.apply(lambda z: calculate_velocity(z.distance, z.timedelta), axis=1)
    df['velocity_next_position'] = df['velocity'].shift(-1)
    df['acceleration'] = df.apply(lambda z: calculate_acceleration(z.velocity, z.velocity_next_position, z.timedelta), axis=1)
    df = df.drop(['velocity_next_position'], axis=1)
    
    df['trajectory_id'] = trajectory_id
    # df['subfolder'] = subfolder
    df['labels'] = ''
    calculate_agg_features(df)
    # result_queue.put(df)
    return df

def load_labels_df(filename):
    df = pd.read_csv(filename, sep='\t')
    df['start_time'] = df['Start Time'].apply(lambda x: dt.datetime.strptime(x, '%Y/%m/%d %H:%M:%S'))
    df['end_time'] = df['End Time'].apply(lambda x: dt.datetime.strptime(x, '%Y/%m/%d %H:%M:%S'))
    df['labels'] = df['Transportation Mode']
    df = df.drop(['End Time', 'Start Time', 'Transportation Mode'], axis=1)
    return df

def calculate_agg_features(df):

    v_ave = np.nanmean(df['velocity'].values)
    v_med = np.nanmedian(df['velocity'].values)
    v_max = np.nanmax(df['velocity'].values)
    a_ave = np.nanmean(df['acceleration'].values)
    a_med = np.nanmedian(df['acceleration'].values)
    a_max = np.nanmax(df['acceleration'].values)
   
    df.loc[:, 'v_ave'] = v_ave
    df.loc[:, 'v_med'] = v_med
    df.loc[:, 'v_max'] = v_max
    df.loc[:, 'a_ave'] = a_ave
    df.loc[:, 'a_med'] = a_med
    df.loc[:, 'a_max'] = a_max

folder = r"C:\Users\Deepanshu Sharma\Downloads\Geolife Trajectories 1.3\Geolife Trajectories 1.3\Data2"

def func(user):
    i=1
    df = pd.DataFrame()
    frames=[]
    for in_file in os.scandir(user):
        if in_file.name == "Trajectory":
            # with open("example.txt","a") as file:
            #     file.write(f"Working on user --> {os.path.basename(user)}\n")
            for plt_file in os.scandir(in_file):
                newdf = load_trajectory_df(plt_file.path)
                newdf["path number"]=i
                frames.append(newdf)
                i=i+1
    df =pd.concat(frames , ignore_index=True)
    if 'labels.txt' in os.listdir(user):
        tempdf = pd.read_csv(os.path.join(user,'labels.txt'),sep ='\t')
        tempdf['start_time'] = tempdf['Start Time'].apply(lambda x: dt.datetime.strptime(x, '%Y/%m/%d %H:%M:%S'))
        tempdf['end_time'] = tempdf['End Time'].apply(lambda x: dt.datetime.strptime(x, '%Y/%m/%d %H:%M:%S'))
        tempdf['labels'] = tempdf['Transportation Mode']
        tempdf = tempdf.drop(['End Time', 'Start Time', 'Transportation Mode'], axis=1)
        for idx in tempdf.index.values:
            st = tempdf.iloc[idx]['start_time']
            et = tempdf.iloc[idx]['end_time']
            labels = tempdf.iloc[idx]['labels']
            if labels:
                df.loc[(df['datetime'] >= st) & (df['datetime'] <= et)  , 'labels'] = labels

    df.to_csv(f'output\\{os.path.basename(user)}.csv')

                

