import os
import socketserver
from threading import Thread

import requests

import env
import webrepl_cli
import websocket, json

# connections = {}
# locks = {}

class service(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(1024).strip().decode("utf-8")
        command = self.data.split("\n")
        result = ""

        print(command)

        # if command[0] == "connect":
        #     result = self.connect(command[1:])
        if command[0] == "connect_test":
            result = self.connect_test(command[1:])
        elif command[0] == "send_to_device":
            result = self.send_to_device(command[1:])
        elif command[0] == "reset":
            result = self.reset(command[1:])
        elif command[0] == "reset_webrepl":
            result = self.reset_webrepl(command[1:])
        # elif command[0] == "disconnect":
        #     result = self.disconnect(command[1:])
        elif command[0] == "upload":
            result = self.upload(command[1:])
        elif command[0] == "heartbeat":
            result = self.heartbeat(command[1:])

        self.request.sendall(result)

    # args: [id, ip]
    # def connect(self, args):
    #     if args[0] not in connections:
    #         try:
    #             connections[args[0]] = websocket.WebSocket()
    #             connections[args[0]].connect("ws://" + args[1] + ":8266")
    #             connections[args[0]].recv()
    #             connections[args[0]].send("secret\n")
    #             connections[args[0]].recv()
    #             connections[args[0]].send("import user, json\r\n")
    #             for x in range(0,len("import user, json") + 2):
    #                 connections[args[0]].recv()
    #             locks[args[0]] = False
    #             return b'true'
    #         except Exception as e:
    #             if args[0] in connections:
    #                 del connections[args[0]]
    #             return(b'false\n' + str(e).encode())
    #     else:
    #         return b'false\nDevice already connected'

    # args: [id, ip]
    # def disconnect(self, args):
    #     if args[0] in connections:
    #         connections[args[0]].close()
    #         del locks[args[0]]
    #         del connections[args[0]]
    #         return b'true'
    #     else:
    #         return b'false\nDevice not connected'

    # args: [id, ip]
    def reset(self, args):
        result = requests.get(f'http://{args[1]}/sys/reset')
        return b'true'
        # if args[0] in connections:
        #     while locks[args[0]]:
        #         pass
        #     locks[args[0]] = True
        #     connections[args[0]].send("import machine\r\n")
        #     connections[args[0]].send("machine.reset()\r\n")
        #     self.disconnect([args[0]])
        #     self.connect([args[0], args[1]])
        #     locks[args[0]] = False
        #     return b'true'
        # else:
        #     return b'false\nDevice not connected'

    # args: [ip]
    def reset_webrepl(self, args):
        conn = websocket.WebSocket()
        conn.connect("ws://" + args[0] + ":8266")
        conn.send("secret\n")
        conn.send("import machine\r\n")
        conn.send("machine.reset()\r\n")
        conn.close()
        return b'true'

    # args: [id, ip, source, destination]
    def upload(self, args):
        id = args[0]
        ip = args[1]
        source = args[2]
        destination = args[3]
        try:
            requests.get(f'http://{args[1]}/sys/kill', timeout=1)
        except:
            pass
        try:
            webrepl_cli.main('secret', ip + ':' + destination, 'put', src_file=source)
            return b'true'
        except Exception as e:
            return b'false'

    # args: [id, ip]
    def connect_test(self, args):
        try:
            result = requests.get(f'http://{args[1]}/sys/test', timeout=1)
        except:
            return b'false'
        return result.content
        # if args[0] in connections:
        #     return b'true'
        # else:
        #     return b'false'

    # args: [id, ip, command, args (string)]
    def send_to_device(self, args):
        result = requests.post('http://' + args[1] + '/' + args[2], data=args[3], timeout=3)
        return result.content
        # args[2] = json.loads(args[2])
        # arg_string = ""
        # for arg in args[2]:
        #     arg_string += str(arg) + ","
        # command = "print(json.dumps(user." + args[1] + "(" + arg_string + ")))"
        #
        # while locks[args[0]]:
        #     pass
        # locks[args[0]] = True
        #
        # ws = connections[args[0]]
        #
        # ws.send(command + "\r\n")
        #
        # result = ""
        # addition = ""
        # while addition != ">>> ":
        #     addition = ws.recv()
        #     result += addition if addition != ">>> " else ""
        #
        # locks[args[0]] = False
        #
        # result_start = result.index("\r\n") + 2
        # result = result[result_start:]
        #
        # return result.encode()

    # args: []
    def heartbeat(self, args):
        return b'OK'

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    HOST, PORT = "localhost", int(env.var("ONEIOT_C_PORT", 1102))
    server = ThreadedTCPServer((HOST, PORT), service)
    try:
        server.serve_forever()
    except Exception as e:
        server.shutdown()
