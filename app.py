## Viktor Mihalovic
## Stela Homework
## 13.1.2023

#all installed imports are in requiremets.txt
import json
import constant
import psycopg2
from config import config

# connect to the PostgreSQL server
params = config()
conn = psycopg2.connect(**params)
cur = conn.cursor()

# Opening JSON file
f = open('include/configClear_v2.json', 'r')  

# returns JSON object as a dictionary
data = json.load(f)

# find out latest id (I am not sure if it is set as auto increment)
cur.execute("SELECT id FROM INTERFACE order by id desc limit 1")
id = cur.fetchall()[0][0] + 1

# here i will store my data and set basic variables
sql = dict()  
port = None
sub = None
port_id = dict()
interfaces = data["frinx-uniconfig-topology:configuration"]["Cisco-IOS-XE-native:native"]["interface"]

# going through dict 
for groups in interfaces:
    conf = interfaces[groups]   # config row
    if groups in constant.WANTED_INTERFACES:   # we are only interested in some interfaces. There are set in constants.py
        for group in interfaces[groups]:
            row = []
            row.append(str(groups) + str(group["name"]))   #name 
            row.append(group.get("description"))   #description
            row.append(group.get("mtu"))    #mtu
            row.append(json.dumps(conf))    # change conf to json and append to my table 

            # here, I am looking for channel group based od the name of key
            sub = [value for key, value in group.items() if 'ethernet:channel-group' in key.lower()]
            if sub:
                port = int(sub[0].get("number")) 
            row.append(port) #add port number to my table (None/port)

            # here i am going to save where port nuumber and id so I can link them later
            if row[0][0:12] == 'Port-channel':
                port_id[int(row[0][12:])] = id

            sql[id] = row   # add to my dict. I need to add all rows and after then, I can change number port to ID of port chanel.
            # reset my variables
            sub = None
            port = None
            row  = []
            id += 1

# here i am going through my dict and looking for ports. When I find a port, I changed it to ID based on port_id dict. 
for row in sql:
    if sql[row][4]:
        sql[row][4] = port_id[sql[row][4]]


# afer all I insert values to database. My table is called interface... 
for row in sql:
    cur.execute("INSERT INTO interface(id,name, description, max_frame_size, config, port_channel_id)VALUES(%s,%s,%s,%s,%s,%s)",(row,sql[row][0],sql[row][1],sql[row][2],sql[row][3],sql[row][4]))
    conn.commit()

# Closing everything
conn.close()
cur.close()

f.close()