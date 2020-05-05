
# coding: utf-8

# ## Portfolio performance chart with Google Charts

# This script takes the file "musterdepot_Komplett_meineuebersicht.csv" and the template "portfolioPerformance_in.html" as input and creates the values for the google bubble chart.    

# In[132]:


import datetime
import pandas as pd
import sys
from numpy import nan as NA
import math


# In[133]:


useQuantiles = True
if len(sys.argv) > 1:
    arg = sys.argv[1] 
else:
    arg=''
if 'absolut' in arg:
    useQuantiles = False


# In[134]:


def floatconv(val):
    try:
        if val.strip():
            return float(val.replace('.','').replace(',','.'))
        else:
            return 0
    except ValueError as ve:
        print("VALUE NOT USABLE for floatconv: #{}#".format(val))


# In[135]:


def percentconv(val):
    try:
        if '%' in val:
            return floatconv(val.replace('%', ''))
        else:
            return NA
    except ValueError as ve:
        print("VALUE NOT USABLE for percentconv: #{}#".format(val))


# Unfortunately we depend on the musterdepot column names given by comdirect.  
# This may lead to problems when column names change.

# In[136]:


intconv = lambda val: 0 if len(str(val)) < 2 else float(str(val).replace('.',''))
converter = {'Aktuell':floatconv, 'Wert in EUR':floatconv, 'Perf. 3 Monate':percentconv,              'Perf. 1 Jahr':percentconv, 'Perf. 3 Jahre':percentconv}


# Sometimes the assets' names change. To be independ of the changes and to have short names fitting to the graphic theres a wkn2names lookup table.

# In[137]:


wkn_to_short = pd.read_csv('wkn2names.csv', header=None, sep=':', index_col=0, squeeze=True).to_dict()

def shortname(longname):
    return wkn_to_short[longname]


# In[138]:


filename = "musterdepot_Komplett_meineuebersicht.csv"
data = pd.read_csv(filename, sep=";", header=2, encoding="iso-8859-1", converters = converter, usecols=["Stück","WKN","Aktuell","Perf. 3 Monate","Perf. 1 Jahr","Perf. 3 Jahre"])
data['Wert'] = data['Stück']*data['Aktuell']
data['Name'] = data['WKN'].apply(lambda x: shortname(x[0:23]))


# In[139]:


data


# Some values may not have been created three years ago. Therefore they don't have a three year performance and the value is NaN. Certainly there are different ways (differently reasonable) to fill this gap. In this case the missing values are replaced by the mean three year performance.

# In[140]:


data['Perf. 3 Jahre'].fillna(data['Perf. 3 Jahre'].mean(),inplace=True)


# In[141]:


data


# If the script is run without parameters, the five color categories will be filled quantiles. I.e. the 20% lowest performing assets will be red, the next 20% will be orange ... and the 20% best performing assets will be dark green. The colors are given in the html template. 

# In[142]:


def perf_to_String(val,quantiles):
    if val < quantiles[0.2]:
        return 'lowest'
    if val < quantiles[0.4]:
        return 'low'
    if val < quantiles[0.6]:
        return 'mid'
    if val < quantiles[0.8]:
        return 'high'
    return 'highest'

def perf_to_Stringabsolut(val):
    if val < -4:
        return 'lowest'
    if val < 0:
        return 'low'
    if val < 2:
        return 'mid'
    if val < 4:
        return 'high'
    return 'highest'


# In[143]:


if useQuantiles == True:
    quantiles = data['Perf. 3 Monate'].quantile([0.2,0.4,0.6,0.8])
    data['Perf3MString'] = data['Perf. 3 Monate'].apply(lambda x: perf_to_String(x,quantiles))
else:
    data['Perf3MString'] = data['Perf. 3 Monate'].apply(lambda x: perf_to_Stringabsolut(x))


# Calculate the performance values for the complete portfolio. The resulting performance values will be used some cells later.

# In[144]:


data['Value3MAgo'] = data['Wert']/(1+data['Perf. 3 Monate']/100)
data['Value1YAgo'] = data['Wert']/(1+data['Perf. 1 Jahr']/100)
data['Value3YAgo'] = data['Wert']/(1+data['Perf. 3 Jahre']/100)

value_today = data['Wert'].sum()
v3mago = data['Value3MAgo'].sum()
v1yago = data['Value1YAgo'].sum()
v3yago = data['Value3YAgo'].sum()
p3m = (value_today/v3mago-1)*100
p1y = (value_today/v1yago-1)*100
p3y = (value_today/v3yago-1)*100
print("Portfolio total value: {0:7.2f}, 3-month-performance: {1:3.2f}% , 1Y-perf: {2:3.2f}%, 3Y-perf: {3:3.2f}%"
      .format(value_today,p3m,p1y,p3y))


# In[145]:


def rd(val):
    return int(round(val))


# Construct the data array to be inserted in the template's function `google.visualization.arrayToDataTable`

# In[146]:


values=""
for i, (index, row) in enumerate(data.sort_values(by=['Perf. 3 Monate']).iterrows()):
    values += "['"+row['Name']+"',"     +str(rd(row['Perf. 3 Jahre']))+","     +str(rd(row['Perf. 1 Jahr']))+",'"     +row['Perf3MString']+"',"     +str(rd(row['Wert']))+"],"     +'\n'

#Portfolio line with 1y and 3y performance and 3m as part of the name (special color)    
values += "['Portfolio 3M:"+str(round(p3m,2))+"%'," +str(rd(p3y))+"," +str(rd(p1y))+"," +"'Portfolio','" +str(int(data['Wert'].sum())) +"']\n"


# Calculate the boundaries:

# In[147]:


x_min = math.floor(data["Perf. 3 Jahre"].min()/10)*10
x_max = math.ceil(data["Perf. 3 Jahre"].max()/10)*10
y_min = math.floor(data["Perf. 1 Jahr"].min()/10)*10
y_max = math.ceil(data["Perf. 1 Jahr"].max()/10)*10


# In[148]:


def round_to_str(number):
    return str(round(number,1))
    
def print_quantiles(quantile_values):
    return ']'+','.join(map(round_to_str, quantile_values))+'['


# In[149]:


def get_range_str(min,max):
    range_str = str(min)
    for i in range(min,max,10):
        range_str=range_str+","+str(i+10)
    return range_str


# Read the template, replace the placeholder and write the output html.

# In[150]:


with open('portfolioPerformance_in.html','rt') as fin, open('portfolioPerformance.html','wt') as fout:
    for line in fin:
        if '#$0' in line:
            line = line.replace('#$0',values) 
        if '#$1' in line:
            today = datetime.date.today()
            line = line.replace('#$1',today.strftime('%d.%m.%Y'))
        if '#$2' in line:
            if useQuantiles == True:
                line = line.replace('#$2',print_quantiles(quantiles.values))
            else:
                line = line.replace('#$2',']-4;0;2;4[')
        if '#$3' in line:
            line = line.replace('#$3',get_range_str(x_min,x_max))
        if '#$4' in line:
            line = line.replace('#$4',get_range_str(y_min,y_max))
        fout.write(line)

