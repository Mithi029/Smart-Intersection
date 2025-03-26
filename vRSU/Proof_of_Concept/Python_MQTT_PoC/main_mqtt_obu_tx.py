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

obu_tempid_file_name = "main_mqtt_obu_TEMPID.txt"

tz_UTC = pytz.timezone('UTC')

broker = 'broker.emqx.io'
port = 1883

obu_publish_topic_prefix = "UserClientToPlatform/"
obu_subscribe_topic_prefix = "PlatformToUserClient/"

# RSU_ID = 2
#
# map_publish_topic = f"{rsu_publish_topic}{RSU_ID}/MAP"
# spat_publish_topic = f"{rsu_publish_topic}{RSU_ID}/SPaT"
# tim_publish_topic = f"{rsu_publish_topic}{RSU_ID}/TIM"
# psm_publish_topic = f"{rsu_publish_topic}{RSU_ID}/PSM"

client_id = f'python-mqtt-{random.randint(0, 100)}'
username = 'emqx'
password = 'public'

# Ieee1609Dot2Data_var = Dot2PayloadOnly.Dot2Data.Ieee1609Dot2Data
messageFrame_var = J2735.DSRC.MessageFrame
SnapShot_var = J2735.DSRC.Snapshot

def create_SnapShot(json_bsm):
    datetime_now = datetime.now(tz_UTC)
    snapshot_dict = {'thePosition':
                         {'utcTime':
                              {'year': datetime_now.year,
                               'month': datetime_now.month,
                               'day': datetime_now.day,
                               'hour': datetime_now.hour,
                               'minute': datetime_now.minute,
                               'second': datetime_now.second,
                               'offset': 0
                               },
                          'long': json_bsm["value"]["coreData"]["long"],
                          'lat': json_bsm["value"]["coreData"]["lat"],
                          'elevation': json_bsm["value"]["coreData"]["elev"],
                          'heading': json_bsm["value"]["coreData"]["heading"],
                          'speed':
                              {'transmisson': 'unavailable',
                               'speed': json_bsm["value"]["coreData"]["speed"]
                               },
                          'posAccuracy':
                              {'semiMajor': json_bsm["value"]["coreData"]["accuracy"]["semiMajor"],
                               'semiMinor': json_bsm["value"]["coreData"]["accuracy"]["semiMinor"],
                               'orientation': json_bsm["value"]["coreData"]["accuracy"]["orientation"]
                               },
                          'timeConfidence': 'unavailable',
                          'posConfidence':
                              {'pos': 'unavailable',
                               'elevation': 'unavailable'
                               },
                          'speedConfidence':
                              {'heading': 'unavailable',
                               'speed': 'unavailable',
                               'throttle': 'unavailable'
                               }
                          }
                     }
    SnapShot_var.set_val(snapshot_dict)
    return binascii.hexlify(SnapShot_var.to_uper())

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


def publish(client, bsm_tempid, payload):
    topic=f'{obu_subscribe_topic_prefix}{bsm_tempid}/UserClientUpload'
    msg = payload
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

def subscribe(client, topic):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    client.subscribe(topic)
    client.on_message = on_message

client = connect_mqtt()
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
#ip = ""
ip = "localhost"
# Listening on all interfaces
server_address = (ip, 12345)
# Listening on port number 12345

print('starting up on %s port %s' % server_address)

sock.bind(server_address)
print("Socket: "+str(sock.getsockname()))

def obu_snapshot_loop():
    bsm_Counter = 0
    while True:
        print('\nwaiting to receive message')
        data, address = sock.recvfrom(4096)

        print('received %s bytes from %s' % (len(data), address))
        # print('Received Raw Data:')
        # print(data)
        if data:
            try:
                messageFrame_var.from_uper(data)
                pass
            except:
                print("Received packet ASN Decode Failed...", sys.exc_info()[0], "occurred.")
                pass
            else:
                messageFrame_json = json.loads(messageFrame_var.to_json())
                # print(messageFrame_json)
                if messageFrame_json["messageId"] == 20:
                    print("Received BSM Payload")
                    bsm_Counter = bsm_Counter + 1
                    OBU_TempID = messageFrame_json["value"]["coreData"]["id"]

                    obu_tempid_file = open(obu_tempid_file_name, "w")
                    obu_tempid_file.write(messageFrame_json["value"]["coreData"]["id"])

                    #out_q.put(OBU_TempID)
                    SnapshotData_uper = create_SnapShot(messageFrame_json).decode("utf-8")
                    if bsm_Counter % 10 == 0:
                        publish(client, OBU_TempID, str(SnapshotData_uper))
                else:
                    print("Received Payload is not a BSM")
        time.sleep(0.001)

# def obu_rx_loop(in_q):
#     while True:
#         OBU_TempID = in_q.get()
#         print(type(OBU_TempID))
#         subscribe(client, 'RoadSideClientToPlatform/2/SPaT')
#         client.loop_forever()

obu_snapshot_thread = threading.Thread(target=obu_snapshot_loop)

# obu_rx_thread = threading.Thread(target=obu_rx_loop, args=(q, ))

obu_snapshot_thread.start()
# obu_rx_thread.start()