import asyncio
import socket
import sys
import ASN_J2735
import json
import time
# sys.path.insert(0, '/opt/smart_intersection')

class SmartIntersection:

    def __init__(self):
        self.ip = '0.0.0.0'
        self.receive_v2x_port = 3366
        self.receive_cv_port = 7788
        self.J2735_messageFrame = ASN_J2735.DSRC.MessageFrame
        self.spat_timings = {}
        self.spat_timings_list = []
        self.ped_interest = ()
        self.event_dict = {}
        self.ped_interest_list = []
        

    async def decode_v2x_messages(self):
        v2x_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        v2x_client.setblocking(False)
        server_address = (self.ip, self.receive_v2x_port)
        v2x_client.bind(server_address)
        loop = asyncio.get_event_loop()
        while True:
            # print('\nwaiting to receive message')
            try:
                data = await loop.sock_recv(v2x_client, 2094)
                # data, address = client.recvfrom(4096)
                pass
            except:
                print("Received recvFrom Exception...", sys.exc_info()[0], "occurred.")
                pass
            else:
                if data:
                    #print('size of data: ', len(data))
                    #print(data)
                    try:
                        self.J2735_messageFrame.from_uper(data)
                    except:
                        print("Received packet J2735 ASN UPER Decode Failed...", sys.exc_info()[0], "occurred.")
                    else:
                        decoded_v2x_json_message = json.loads(self.J2735_messageFrame.to_json())

                        if decoded_v2x_json_message["messageId"] == 18:
                            print('Received MAP')
                            # print(decoded_v2x_json_message['value']['intersections'][0]['id'])
                            # print(decoded_v2x_json_message['value']['intersections'][0]['refPoint'])
                            self.ped_interest_list.clear()
                            for i in range(len(decoded_v2x_json_message['value']['intersections'][0]['laneSet'])):
                                self.lane_id = decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]['laneID']
                                self.lane_type = decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]['laneAttributes']['laneType']
                                
                                if 'connectsTo' in decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]:
                                    
                                    for j in range(len(decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]['connectsTo'])):
                                        if 'crosswalk' in self.lane_type or 'sidewalk' in self.lane_type:
                                            # print('laneID: ', self.lane_id)
                                            # print('lane_type: ', self.lane_type)
                                            # print(decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]['connectsTo'][j])
                                            self.map_sgnl_grp_id = decoded_v2x_json_message['value']['intersections'][0]['laneSet'][i]['connectsTo'][j]['signalGroup']
                                            #print('connecting using signal group ID: ', self.map_sgnl_grp_id)
                                            self.ped_interest = (self.lane_id, self.map_sgnl_grp_id)
                                            self.ped_interest_list.append(self.ped_interest)
                                            # print('pedestrian - (laneID, SignalGrpID): ', self.ped_interest)
                                #         else:
                                #             print('its a vehicle or a bike lane, not interested for now...!!')
                                # else:
                                #     print('this lane is not connecting anyone')
                                #print('---------------------------------------------------------------------')
                        elif decoded_v2x_json_message["messageId"] == 19:
                            print('Received SPaT')
                            intersection_id = decoded_v2x_json_message['value']['intersections'][0]['id']['id']
                            moy = decoded_v2x_json_message['value']['intersections'][0]['moy']
                            timestamp = decoded_v2x_json_message['value']['intersections'][0]['timeStamp']
                            for i in range(len(decoded_v2x_json_message['value']['intersections'][0]['states'])):
                                signl_grp = decoded_v2x_json_message['value']['intersections'][0]['states'][i]['signalGroup']
                                event_state = decoded_v2x_json_message['value']['intersections'][0]['states'][i]['state-time-speed'][0]['eventState']
                                # print(decoded_v2x_json_message['value']['intersections'][0]['states'][i]['state-time-speed'][0]['timing'])
                                max_end_time = decoded_v2x_json_message['value']['intersections'][0]['states'][i]['state-time-speed'][0]['timing']['maxEndTime']
                                max_end_time = self.time_conversion(max_end_time)
                                min_end_time = decoded_v2x_json_message['value']['intersections'][0]['states'][i]['state-time-speed'][0]['timing']['minEndTime']
                                min_end_time = self.time_conversion(min_end_time)
                                # print(signl_grp)
                                self.event_dict = {
                                    event_state: [min_end_time, max_end_time]
                                }
                                self.spat_timings = {
                                    signl_grp: self.event_dict
                                }
                                # print(self.spat_timings)
                                # print('------------------------------------------------------------------------------------')
                                self.spat_timings_list.append(self.spat_timings)
                            self.decoded_spat = {
                                'Intersection ID': intersection_id,
                                'Minute of the year': moy,
                                'timestamp': timestamp, 
                                'spat_timings': self.spat_timings_list
                            }
                            # print(self.decoded_spat)
                        else:
                            pass
                            #print(decoded_v2x_json_message)
                    time.sleep(0.2)
                    

                else:
                    print("No Data received")
                await asyncio.sleep(0.01)
        
    
    def time_conversion(self, t):
        t_min = int(t) / 600
        fractional_part = t_min - int(t_min)
        seconds = fractional_part * 60
        t_sec = int(seconds)
        timestamp = str(int(t_min))+':'+str(t_sec)
        return timestamp

    async def decode_cv_objects(self):
        cv_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cv_client.setblocking(False)
        pi_details = (self.ip, self.receive_cv_port)
        cv_client.bind(pi_details)
        loop = asyncio.get_event_loop()
        while True:
            data = await loop.sock_recv(cv_client, 1024)
            # data, addr = client.recvfrom(1024)
            try:
                json_obj = json.loads(data.decode())
                # print(len(json_obj))
                for k, v in json_obj.items():
                    # print(k: v)
                    if v[0] == 0 and v[2] > 60:
                        print('found a person in the crossbar...!!!')
                        # return True
                    elif v[0] == 0 and v[2] < 59:
                        print('Not sure if this is a person')

            except json.JSONDecodeError as e:
                print(e)
    
    async def filter_out_data(self):
        # know signal group from 
        while True: 
            # print(self.ped_interest_list)
            for i in range(len(self.ped_interest_list)):
                if self.ped_interest_list[i][0] == 36:
                    for j in range(len(self.spat_timings_list)):
                        
                        if self.ped_interest_list[i][1] in self.spat_timings_list[j]:
                            print(self.spat_timings_list[j])

            await asyncio.sleep(1)
            # if self.ped_interest[0] == '36':
            #     


        # find its corresponding state and time in SPAT
        # 
        
        #
        # if person is detected
        # 
        # send this info to mqtt broker / remote server
        # 
        # generate PSM (alt)  
        

if __name__ == "__main__":
    decode = SmartIntersection()
    async def thread_exec():
        await asyncio.gather(
            decode.decode_v2x_messages(),
            # decode.decode_cv_objects(),
            decode.filter_out_data()
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(thread_exec())


    


