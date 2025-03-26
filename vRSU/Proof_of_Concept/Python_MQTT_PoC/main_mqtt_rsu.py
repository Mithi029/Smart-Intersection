import socket
import sys
import J2735
import Dot2PayloadOnly
import json
import binascii
import time
import random
from paho.mqtt import client as mqtt_client

broker = 'broker.emqx.io'
# broker = 'est-csvis001.danlawinc.com'
# port = 5672
port = 1883

rsu_publish_topic = "RoadSideClientToPlatform/"

RSU_ID = 2

map_publish_topic = f"{rsu_publish_topic}{RSU_ID}/MAP"
spat_publish_topic = f"{rsu_publish_topic}{RSU_ID}/SPaT"
tim_publish_topic = f"{rsu_publish_topic}{RSU_ID}/TIM"
psm_publish_topic = f"{rsu_publish_topic}{RSU_ID}/PSM"

client_id = f'{RSU_ID}'
username = 'emqx'
password = 'public'
# username = 'mqtt-test'
# password = 'mqtt-test'

Ieee1609Dot2Data_var = Dot2PayloadOnly.Dot2Data.Ieee1609Dot2Data
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


def publish(client, topic, payload):
    msg = payload
    result = client.publish(topic, msg, qos=1, retain=True)
    print(type(result))
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")

client = connect_mqtt()
# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
ip = ""
# ip = "localhost"
# Listening on all interfaces
server_address = (ip, 12345)
# Listening on port number 12345

print('starting up on %s port %s' % server_address)

sock.bind(server_address)
print("Socket: "+str(sock.getsockname()))

while True:
    print('\nwaiting to receive message')
    data, address = sock.recvfrom(4096)

    print('received %s bytes from %s' % (len(data), address))
    # print('Received Raw Data:')
    # print(data)

    if data:
        try:
            Ieee1609Dot2Data_var.from_oer(data)
            pass
        except:
            print("Received packet ASN Decode Failed...", sys.exc_info()[0], "occurred.")
            pass
        else:
            Ieee1609Dot2Data_json = json.loads(Ieee1609Dot2Data_var.to_json())
            Ieee1609Dot2Data_content = Ieee1609Dot2Data_json["content"]

            if ("unsecuredData" in Ieee1609Dot2Data_content) | ("signedData" in Ieee1609Dot2Data_content):
                if "unsecuredData" in Ieee1609Dot2Data_content:
                    print("Unsigned Payload")
                    Dot2UnsignedPayload = Ieee1609Dot2Data_content["unsecuredData"]
                    # print(type(Dot2UnsignedPayload))
                elif "signedData" in Ieee1609Dot2Data_content:
                    print("Received Signed Payload")
                    Dot2UnsignedPayload = Ieee1609Dot2Data_content["signedData"]["tbsData"]["payload"]["data"]["content"]["unsecuredData"]
                    # print(type(Dot2UnsignedPayload))
                try:
                    messageFrame_var.from_uper(binascii.unhexlify(Dot2UnsignedPayload))
                    pass
                except:
                    print("Received packet ASN Decode Failed...", sys.exc_info()[0], "occurred.")
                    pass
                else:
                    messageFrame_json = json.loads(messageFrame_var.to_json())
                    # print(messageFrame_json)
                    if messageFrame_json["messageId"] == 18:
                        print("Received MAP Payload")
                        # print(messageFrame_json["value"]["intersections"][0]["id"]["id"])
                        if messageFrame_json["value"]["intersections"][0]["id"]["id"] == RSU_ID:
                            publish(client, map_publish_topic, Dot2UnsignedPayload)
                        else:
                            print("Received MAP Payload not matching RSU_ID")
                    elif messageFrame_json["messageId"] == 31:
                        print("Received TIM Payload")
                        publish(client, tim_publish_topic, Dot2UnsignedPayload)
                    elif messageFrame_json["messageId"] == 19:
                        print("Received SPaT Payload")
                        if messageFrame_json["value"]["intersections"][0]["id"]["id"] == RSU_ID:
                            publish(client, spat_publish_topic, Dot2UnsignedPayload)
                        else:
                            print("Received SPaT Payload not matching RSU_ID")
                    elif messageFrame_json["messageId"] == 32:
                        print("Received PSM Payload")
                        publish(client, psm_publish_topic, Dot2UnsignedPayload)
                    else:
                        print("Received Payload which is not MAP | TIM | SPaT | PSM")
            else:
                print("UnRecognized Payload")
    time.sleep(0.001)