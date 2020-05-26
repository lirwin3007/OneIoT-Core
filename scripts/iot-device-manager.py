import os
import re
import json
import uuid
import serial
import os.path as path

import serial.tools.list_ports

import oneiot_core.env as env
import oneiot.EventBus as EventBus

addDeviceRequests = {}
stageCount = 5

steps = {
    1: {
        'id': 'unplug_device',
        'instruction': 'Please ensure your device is unplugged.',
        'required_info': [],
        'stage': {
            'current': 1,
            'count': stageCount
        }
    },
    2: {
        'id': 'plug_in_device',
        'instruction': 'Please now plug in the device.',
        'required_info': [],
        'stage': {
            'current': 2,
            'count': stageCount
        }
    },
    3: {
        'id': 'naming',
        'instruction': 'Provide some information about the device.',
        'required_info': [
            {
                'id': 'id',
                'prompt': 'Unique ID',
                'type': 'text',
                'tip': 'Each device needs its own unique ID. Use only a-z, underscores and dashes'
            }
        ],
        'stage': {
            'current': 3,
            'count': stageCount
        }
    }
}

# Log to an event bus
def logToEB(eb, id, type, message):
    eb.send(id, {
        'type': type,
        'message': message
    })

# Initialise the request to add a device
def initAddDevice(id, data, eb):
    token = uuid.uuid1().hex
    while token in addDeviceRequests:
        token = uuid.uuid1().hex
    addDeviceRequests[token] = {
        'ports': []
    }
    eb.send(f'device_manager.add_device.{token}.confirm', {'next_step': steps[1]})

# Carry out the stages of adding a device
def addDevice(id, data, eb):
    stage = id.split('.')[-1]
    token = id.split('.')[-2]
    if token not in addDeviceRequests:
        return
    requestData = addDeviceRequests[token]
    if stage == 'unplug_device':
        requestData['ports'] = [x.name for x in serial.tools.list_ports.comports()]
        eb.send(f'device_manager.add_device.{token}.log', {
            'type': 'info',
            'message': f'Found COM ports: {requestData["ports"]}'
        })
        eb.send(f'device_manager.add_device.{token}.confirm', {'next_step': steps[2]})
    if stage == 'plug_in_device':
        success = False
        newPorts = [x.name for x in serial.tools.list_ports.comports()]
        portsDiff = list(set(newPorts) - set(requestData['ports']))

        if len(portsDiff) == 0:
            eb.send(f'device_manager.add_device.{token}.log', {
                'type': 'error',
                'message': f'Could not find device. Resetting to step 1'
            })
            eb.send(f'device_manager.add_device.{token}.confirm', {'next_step': steps[1]})
        elif len(portsDiff) > 1:
            eb.send(f'device_manager.add_device.{token}.log', {
                'type': 'error',
                'message': f'Other devices have been plugged in alongside target device. Resetting to step 1'
            })
            eb.send(f'device_manager.add_device.{token}.confirm', {'next_step': steps[1]})
        else:
            requestData['port'] = portsDiff[0]
            eb.send(f'device_manager.add_device.{token}.log', {
                'type': 'info',
                'message': f'Found device on {requestData["port"]}'
            })
            # Flash Device
            try:
                # Connect
                logToEB(eb, f'device_manager.add_device.{token}.log', 'info', f'Connecting to device on {requestData["port"]}...')
                conn = serial.Serial('/dev/' + requestData['port'], 115200, timeout=1)
                logToEB(eb, f'device_manager.add_device.{token}.log', 'info', f'Connected')

                # Setup WebRepl config file
                logToEB(eb, f'device_manager.add_device.{token}.log', 'info', f'Setting up WebREPL config file')
                passw = uuid.uuid1().hex
                requestData['webREPLPasswd'] = passw
                conn.writelines([str.encode('webreplConf = open("webrepl_cfg.py", "wb")\r\n')])
                conn.writelines([str.encode(f'webreplConf.write("PASS=\'{passw}\'")\r\n')])
                conn.writelines([str.encode('webreplConf.close()\r\n')])

                # Setup boot file
                logToEB(eb, f'device_manager.add_device.{token}.log', 'info', f'Setting up boot.py')
                ssid = env.var('ONEIOT_C_NETWORK_SSID')
                passw = env.network_password()
                conn.writelines([str.encode('boot = open("boot.py", "wb")\r\n')])
                conn.writelines([str.encode('boot.write("import network\\n")\r\n')])
                conn.writelines([str.encode('boot.write("wlan=network.WLAN(network.STA_IF)\\n")\r\n')])
                conn.writelines([str.encode('boot.write("wlan.active(True)\\n")\r\n')])
                conn.writelines([str.encode(f'boot.write("wlan.connect(\'{ssid}\', \'{passw}\')\\n")\r\n')])
                #conn.writelines([str.encode('boot.write("wlan.ifconfig((\'' + device.ip + '\',\'255.255.255.0\',\'192.168.4.1\',\'8.8.8.8\'))\\n")\r\n')])
                conn.writelines([str.encode('boot.write("import webrepl\\n")\r\n')])
                conn.writelines([str.encode('boot.write("webrepl.start()\\n")\r\n')])
                conn.writelines([str.encode('boot.close()\r\n')])

                # Reset
                logToEB(eb, f'device_manager.add_device.{token}.log', 'info', f'Resetting device on {requestData["port"]}')
                conn.writelines([str.encode('import machine\r\n')])
                conn.writelines([str.encode('machine.reset()\r\n')])
                success = True
            except Exception as err:
                logToEB(eb, f'device_manager.add_device.{token}.log', 'error', str(err))
            finally:
                # Close Serial Connection
                logToEB(eb, f'device_manager.add_device.{token}.log', 'info', f'Closing connection on {requestData["port"]}...')
                conn.close()
                logToEB(eb, f'device_manager.add_device.{token}.log', 'info', f'Closed')
        if success:
            eb.send(f'device_manager.add_device.{token}.confirm', {'next_step': steps[3]})
    if stage == "naming":
        if not path.exists(f'{path.expanduser("~")}/.oneIot/devices'):
            os.mkdir(f'{path.expanduser("~")}/.oneIot/devices')

        if 'id' not in data:
            logToEB(eb, f'device_manager.add_device.{token}.log', 'error', 'Device ID not provided')
            eb.send(f'device_manager.add_device.{token}.confirm', {'next_step': steps[3]})
        elif not re.match("^[a-z_-]*$", data['id']):
            logToEB(eb, f'device_manager.add_device.{token}.log', 'error', f'Device ID can only contain a-z (lowercase), dashes and underscores.')
            eb.send(f'device_manager.add_device.{token}.confirm', {'next_step': steps[3]})
        elif path.exists(f'{path.expanduser("~")}/.oneIot/devices/{data["id"]}.json'):
            logToEB(eb, f'device_manager.add_device.{token}.log', 'error', f'Device ID "{data["id"]}" already taken')
            eb.send(f'device_manager.add_device.{token}.confirm', {'next_step': steps[3]})
        else:
            with open(f'{path.expanduser("~")}/.oneIot/devices/{data["id"]}.json', 'w') as deviceFile:
                json.dump({
                    'id': data["id"],
                    'webprel_password': requestData['webREPLPasswd']
                }, deviceFile)
            eb.send(f'device_manager.add_device.{token}.complete')
            del addDeviceRequests[token]


if __name__ == "__main__":
    # Initialise the event bus
    eb = EventBus(core_ip="localhost")
    eb.connect()

    # Add event callbacks
    eb.on('device_manager.add_device', initAddDevice)
    eb.on('device_manager.add_device.*.*', addDevice)