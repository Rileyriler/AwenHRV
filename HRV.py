import xml.etree.ElementTree as ET
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
plt.style.use("fivethirtyeight")

# ======================================================================
# ====================== ONLY NEED TO EDIT HERE ========================
FILE_NAME = '/Users/rileynoon/Desktop/Awen_HRV/Sensor Data/001_80101.csv'
START_DATE = '2022-10-24 15:07:00'
END_DATE = '2022-10-24 15:24:00'
IMAGE_NAME = '30068.jpg'
# ======================================================================

# figure out which type of file is being inputted
file_type = FILE_NAME.split(".")[-1]

# If we are pulling data from an Apple Watch:
if file_type == "xml":
    # create element tree object
    # parser = ET.XMLParser(encoding="utf-8")
    tree = ET.parse(FILE_NAME) 

    # for every health record, extract the attributes
    root = tree.getroot()
    record_list = [x.attrib for x in root.iter('Record')]
    record_data = pd.DataFrame(record_list)

    # proper type to dates
    for col in ['creationDate', 'startDate', 'endDate']:
        record_data[col] = pd.to_datetime(record_data[col])

    # value is numeric, NaN if fails
    record_data['value'] = pd.to_numeric(record_data['value'], errors='coerce')

    # some records do not measure anything, just count occurences
    # filling with 1.0 (= one time) makes it easier to aggregate
    record_data['value'] = record_data['value'].fillna(1.0)

    # shorter observation names (these 2 lines help prevent future errors)
    record_data['type'] = record_data['type'].str.replace('HKQuantityTypeIdentifier', '')
    record_data['type'] = record_data['type'].str.replace('HKCategoryTypeIdentifier', '')

    #only keep heart rate data
    HeartRate = record_data[record_data['type'] == "HeartRate"] 
    HeartRate = HeartRate[['type','startDate','value']]

    #select data of a specific VR experience

    mask = (HeartRate['startDate'] >= START_DATE) & (HeartRate['startDate'] <= END_DATE)

    HeartRate = HeartRate.loc[mask]

    HeartRate['Date_int'] = HeartRate['startDate'].astype(np.int64)
    HeartRate['Date_ms'] = HeartRate['Date_int']/1000000000
    #export seleted raw heart rate data
    HeartRate.to_csv('HeartRate.csv')

    #calculate heart rate variability
    HeartRate["previous_value"] = HeartRate["value"].shift(1)

    HeartRate["Diff"] = HeartRate["value"] - HeartRate["previous_value"]

    HeartRate = HeartRate.set_index('Date_ms')

    HeartRate['minutes'] = pd.cut(HeartRate.index, bins=[HeartRate.index[0],HeartRate.index[0]+180, HeartRate.index[0]+360,HeartRate.index[0]+540, HeartRate.index[0]+719,HeartRate.index[0]+900, HeartRate.index[0]+1080, HeartRate.index[0]+1260], labels=['0 min', '3 min', '6 min', '9 min', '12 min', '15 min', '18 min'])

    HeartRate = HeartRate.set_index('startDate')
    HeartRate['count'] = HeartRate.index.minute
    d = HeartRate['count'].value_counts()

    HeartRate['duplicate'] = HeartRate['count'].map(d)

    # This line cleans out any minute that does not have enough data points (i.e. only minutes with 6+ entries will be counted)
    HeartRate = HeartRate[HeartRate['duplicate'] > 6] 

    STD = HeartRate.groupby('minutes')['Diff'].std()
    STD = STD/60*1000

    #STD = HeartRate['Diff'].resample('2T').std()
    #STD = STD/60*1000

    # Creating the graph
    fig, ax = plt.subplots(1, 1)

    STD_ = STD.copy()
    STD_[0] = np.nan
    print(STD)
    STD.plot(linewidth = 2) 
    ax.set_ylim(0, 100)

    x = [0.33, 0.33]
    y = [0, 130]
    plt.plot(x,y, linewidth=2)
    x = [4.66, 4.66]
    y = [0, 130]
    plt.plot(x,y, linewidth=2)

    plt.text(0.2, 70, 'Pre-experience', rotation = 90, size = '10')
    plt.text(2, 83, 'Experience', size='10')
    plt.text(4.66, 70, 'Post-experience', rotation = 270, size = '10')


    plt.title("Heart Rate Variability with Time", size = '12')
    plt.grid(linewidth = 0.5, linestyle = '--')
    plt.tight_layout()
    ax.set_ylabel('Heart Rate Varibility (milliseconds)', size=10)
    ax.set_xlabel('Time',size=10)

    #export graph to image
    fig1 = plt.gcf()
    fig1.savefig(IMAGE_NAME)


    plt.show()

# If we are pulling data from Shimmer instead of Apple Watch:    
elif file_type == "csv":
    record_data = pd.read_csv(FILE_NAME)

    # set the index so we can collect relevant data about the participant, and adding column names so we can pull data more easily
    record_data = record_data.set_index("#INFO")
    record_data.rename(columns={record_data.columns[1] :'col 1', record_data.columns[2]:'col 2'}, inplace=True)

    # collect relevant data
    respondent_name = record_data.loc["#Respondent Name", "col 1"]
    respondent_group = record_data.loc["#Respondent Group", "col 1"]
    recording_date = record_data.loc["#Recording time", "col 1"]
    recording_time = record_data.loc["#Recording time", "col 2"]

    # set column headers
    record_data.columns = record_data.iloc[25]

    # delete unnecessary rows and columns
    record_data = record_data.iloc[26:]
    record_data = record_data.drop(columns=['Combined Event Source', 'SlideEvent', 'StimType', 'Duration', 'CollectionPhase', 'SourceStimuliName', 'InputEventSource', 'Data', 'StimType', 'Event Group', 'Event Label', 'Event Text', 'Event Index', 'SampleNumber', 'Timestamp RAW', 'System Timestamp CAL', 'Timestamp CAL', 'Internal ADC A13 PPG RAW', 'Internal ADC A13 PPG CAL','IBI PPG ALG','Packet reception rate RAW'])

    # convert strings to numeric
    record_data["Heart Rate PPG ALG"] = pd.to_numeric(record_data["Heart Rate PPG ALG"], errors='coerce')

    # delete any rows with no recorded value for BPM (i.e. -1)
    record_data = record_data[record_data["Heart Rate PPG ALG"] > 0]




    
    print("hi")