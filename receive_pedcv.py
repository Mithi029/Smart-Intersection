import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ip = '0.0.0.0'
port = 7788
pi_details = (ip, port)
sock.bind(pi_details)

while True:
    data, addr = sock.recvfrom(1024)

    try:
        json_obj = json.loads(data.decode())
        print(json_obj)

    except json.JSONDecodeError as e:
        print(e)

