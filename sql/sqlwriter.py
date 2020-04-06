from time import localtime, strftime
import paho.mqtt.client as mqtt
import sqlite3
import time

#topic name is configurable using the chirpstack websocket. "#" is a wildcard
#that will catch all mqtt communcation that starts with application/2/device
topic = "application/2/device/#"
#dbFile must be in the same directory as this script. Use the sqlite3 enviroment to make
#a table named "sensor_data" to store data.
dbFile = "data.db"

dataTuple = [-1,-1]

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    theTime = strftime("%Y-%m-%d %H:%M:%S", localtime())

    result = (theTime + "\t" + str(msg.payload))
    print(msg.topic + ":\t" + result)
    dataTuple[0] = str(msg.payload)
    writeToDb(theTime, dataTuple[0])

def writeToDb(theTime, temperature):
    conn = sqlite3.connect(dbFile)
    c = conn.cursor()
    print "Writing to DB"
    #all data that is recieved as one string. The string must be split up into the various components
    #to extract the data.
    data_matrix = temperature.split('"')
    applicationID = data_matrix[3]
    applicationName = data_matrix[7]
    deviceName = data_matrix[11]
    devEUI = data_matrix[15]
    frequencyStr = data_matrix[20]
    frequencyStr = frequencyStr.split(',')
    frequencyStr = frequencyStr[0].replace(":","")
    frequencyInt = int(frequencyStr)
    countStr =  data_matrix[26]
    countStr = countStr.replace(":","")
    countStr = countStr.replace(",","")
    countInt = int(countStr)
    sensor_obj = data_matrix[36]
    sensor_obj = sensor_obj.replace(":","")
    sensor_obj = sensor_obj.replace("}","")
    sensor_obj = float(sensor_obj)
    #the table fields must match the values used to create the table in data.db
    c.execute("INSERT INTO sensor_data VALUES (?, ?, ?, ?, ?, ?, ?, ?) ", (theTime, applicationID, applicationName,
              deviceName, devEUI, frequencyInt, countInt, sensor_obj))
    conn.commit()
    print("Success!")

    global dataTuple
    dataTuple = [-1, -1]
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
time.sleep(1)
client.connect("localhost", 1883, 60)                                                                                                                                                                                                       $
# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()

