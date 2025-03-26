import socket
import sys
import J2735
import Dot2PayloadOnly
import json
import binascii
import random
from paho.mqtt import client as mqtt_client
from datetime import datetime
import pytz
import time
import threading
from queue import Queue

OBU_TempID = "5143DADA"

OBU_IP = '192.168.74.96'
OBU_PORT = 43434

server_address = (OBU_IP, OBU_PORT)

tz_UTC = pytz.timezone('UTC')

broker = 'broker.emqx.io'
port = 1883

obu_publish_topic_prefix = "UserClientToPlatform/"
obu_subscribe_topic_prefix = "PlatformToUserClient/"

client_id = f'python-mqtt-{random.randint(0, 100)}'
username = 'emqx'
password = 'public'

# Ieee1609Dot2Data_var = Dot2PayloadOnly.Dot2Data.Ieee1609Dot2Data
messageFrame_var = J2735.DSRC.MessageFrame

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client, topic):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        # sock.sendto(bytes(msg.payload.decode(), "utf-8"), (OBU_IP, OBU_PORT))
        #print(binascii.unhexlify(msg.payload.decode()))
        sock.sendto(binascii.unhexlify(msg.payload.decode()), (OBU_IP, OBU_PORT))
    client.subscribe(topic)
    client.on_message = on_message

client = connect_mqtt()
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def obu_rx_loop():
    subscribe(client, [('RoadSideClientToPlatform/2/SPaT', 1), ('RoadSideClientToPlatform/2/MAP', 1), ('RoadSideClientToPlatform/2/TIM', 1), ('RoadSideClientToPlatform/2/PSM', 1)])
    #subscribe(client, f'PlatformToUserClient/{OBU_TempID}/SubscribedPayload')
    client.loop_forever()

# obu_snapshot_thread = threading.Thread(target=obu_snapshot_loop)

obu_rx_thread = threading.Thread(target=obu_rx_loop)

# obu_snapshot_thread.start()
obu_rx_thread.start()