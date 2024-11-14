import socket
import sys
import ASN_J2735
import json
import time
# sys.path.insert(0, '/opt/smart_intersection')

class v2xDecode:

    def __init__(self):
        self.ip = '127.0.0.1'
        self.message_receive_port = 3366
        self.J2735_messageFrame = ASN_J2735.DSRC.MessageFrame
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0
        self.data_to_drone = []
        self.list_of_all_txts = []

    def decode_v2x_messages(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)

        server_address = (self.ip, self.message_receive_port)

        print('starting up on %s port %s' % server_address)

        sock.bind(server_address)
        print("Socket: " + str(sock.getsockname()))

        while True:
            # print('\nwaiting to receive message')
            try:
                data, address = sock.recvfrom(4096)
                pass
            except:
                print("Received recvFrom Exception...", sys.exc_info()[0], "occurred.")
                pass
            else:
                if data:
                    print('size of data: ', len(data))
                    # print(data)
                    try:
                        self.J2735_messageFrame.from_uper(data)
                    except:
                        print("Received packet J2735 ASN UPER Decode Failed...", sys.exc_info()[0], "occurred.")
                    else:
                        decoded_v2x_json_message = json.loads(self.J2735_messageFrame.to_json())
                        if decoded_v2x_json_message["messageId"] == 20:
                            print(
                                'Received BSM====> [TempID: %s, msgCnt: %s, secMark: %s, lat: %s, long: %s, speed: %s, '
                                'heading: %s, vehicle_length: %s, vehicle_width: %s]' % (
                                    decoded_v2x_json_message["value"]["coreData"]["id"],
                                    decoded_v2x_json_message["value"]["coreData"]["msgCnt"],
                                    decoded_v2x_json_message["value"]["coreData"]["secMark"],
                                    decoded_v2x_json_message["value"]["coreData"]["lat"],
                                    decoded_v2x_json_message["value"]["coreData"]["long"],
                                    decoded_v2x_json_message["value"]["coreData"]["speed"],
                                    decoded_v2x_json_message["value"]["coreData"]["heading"],
                                    decoded_v2x_json_message["value"]["coreData"]["size"]["length"],
                                    decoded_v2x_json_message["value"]["coreData"]["size"]["width"]))
                        elif decoded_v2x_json_message["messageId"] == 31:
                            advisory_list = decoded_v2x_json_message['value']["dataFrames"][0]['content']['advisory']
                            self.list_of_all_txts = []
                            for i in range(1, len(advisory_list)):
                                adv_messge = \
                                    decoded_v2x_json_message['value']["dataFrames"][0]['content']['advisory'][i][
                                        'item']['text']
                                messages = adv_messge.split(' ')
                                self.latitude = float(messages[0].split(',')[0]) / 10000000
                                self.longitude = float(messages[1].split(',')[0]) / 10000000
                                self.elevation = int(messages[2]) / 10

                        elif decoded_v2x_json_message["messageId"] == 18:
                            print('Received MAP')
                            print('MAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAP')
                            print(decoded_v2x_json_message['value']['intersections'][0]['id'])
                            print(decoded_v2x_json_message['value']['intersections'][0]['refPoint'])
                            for i in range(len(decoded_v2x_json_message['value']['intersections'][0]['laneSet'])):
                                print(decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]['laneID'])
                                print(decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]['laneAttributes']['laneType'])
                                if 'connectsTo' in decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]:
                                    for j in range(len(decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]['connectsTo'])):
                                        print(decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]['connectsTo'][j])
                                else:
                                    print('this lane is not connecting anyone')
                                print('---------------------------------------------------------------------')
                            print('MAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAPMAP')
                        elif decoded_v2x_json_message["messageId"] == 19:
                            print('Received SPaT')
                            print('SPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPAT')
                            print(decoded_v2x_json_message['value']['intersections'][0]['id'])
                            print(decoded_v2x_json_message['value']['intersections'][0]['status'])
                            print(decoded_v2x_json_message['value']['intersections'][0]['moy'])
                            print(decoded_v2x_json_message['value']['intersections'][0]['timeStamp'])
                            for i in range(len(decoded_v2x_json_message['value']['intersections'][0]['states'])):
                                print(decoded_v2x_json_message['value']['intersections'][0]['states'][i]['signalGroup'])
                                print(decoded_v2x_json_message['value']['intersections'][0]['states'][i]['state-time-speed'][0]['eventState'])
                                print(decoded_v2x_json_message['value']['intersections'][0]['states'][i]['state-time-speed'][0]['timing'])
                                print(decoded_v2x_json_message['value']['intersections'][0]['states'][i]['maneuverAssistList'])
                                print('------------------------------------------------------------------------------------')
                            print('SPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPATSPAT')

                        elif decoded_v2x_json_message["messageId"] == 32:
                            print('Received PSM')
                        elif decoded_v2x_json_message["messageId"] == 16:
                            print('Received traveller')
                        elif decoded_v2x_json_message["messageId"] == 20:
                            print('Received vinfo')
                        else:
                            pass
                            # print(decoded_v2x_json_message)
                    time.sleep(0.2)

                else:
                    print("No Data received")


if __name__ == "__main__":
    decode = v2xDecode()
    decode.decode_v2x_messages()
