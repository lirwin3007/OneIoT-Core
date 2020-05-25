import configparser
import os
import stat
import os.path as path

from pystemd.systemd1 import Unit

def get_status():
    # Get setup status
    service_file_created_status = get_service_file_created_status()
    service_is_enabled = check_service_is_enabled()
    # Get executing status
    service_is_running = check_service_is_running()
    return {"setup": [
            {"name": "Core Service unit file exists", "status": service_file_created_status},
            {"name": "Core Service starts on boot", "status": service_is_enabled},
        ],
        "execution": [
            {"name": "Core Service is running", "status": service_is_running},
        ]
    }

def get_service_file_created_status():
    if not path.exists("/lib/systemd/system/oneiotcore.service"):
        return False
    unit_file = configparser.RawConfigParser()
    unit_file.optionxform = str
    unit_file.read('/lib/systemd/system/oneiotcore.service')

    sections = unit_file.sections()
    result = 'Unit' in sections
    result = result and 'Service' in sections
    result = result and 'Install' in sections
    if not result:
        return False

    result = 'After' in unit_file['Unit']
    result = result and 'Type' in unit_file['Service']
    result = result and 'ExecStart' in unit_file['Service']
    result = result and 'WantedBy' in unit_file['Install']
    if not result:
        return False

    result = unit_file['Unit']['After'] == "multi-user.target"
    result = result and unit_file['Service']['Type'] == "idle"
    result = result and unit_file['Service']['ExecStart'] == "iot-core-serve"
    result = result and unit_file['Install']['WantedBy'] == "multi-user.target"

    st = os.stat("/lib/systemd/system/oneiotcore.service")
    result = result and st.st_mode & stat.S_IRUSR
    result = result and (st.st_mode & stat.S_IWUSR)
    result = result and (st.st_mode & stat.S_IRGRP)
    result = result and (st.st_mode & stat.S_IROTH)

    return result

def check_service_is_enabled():
    result = os.system('systemctl is-enabled oneiotcore.service > /dev/null')
    return result == 0

def check_service_is_running():
    result = os.system('systemctl status oneiotcore.service > /dev/null')
    return result == 0

def create_service_unit_file():
    if get_service_file_created_status():
        return
    print("Creating service unit file...")
    unit_file = configparser.RawConfigParser()
    unit_file.optionxform = str
    unit_file['Unit'] = {
        'Description': 'OneIoT Core',
        'After': 'multi-user.target'
    }
    unit_file['Service'] = {
        'Type': 'idle',
        'ExecStart': 'iot-core-serve'
    }
    unit_file['Install'] = {
        'WantedBy': 'multi-user.target'
    }
    with open('/lib/systemd/system/oneiotcore.service', 'w') as configfile:
        unit_file.write(configfile)
    print("... created!")

def start_core_on_boot():
    if check_service_is_enabled():
        return
    print("Enabling service on boot...")
    os.system('systemctl enable oneiotcore.service')
    print("... done!")

def start_core():
    if check_service_is_running():
        return
    print("Starting OneIoT Core...")
    os.system('systemctl start oneiotcore.service')
    print("... done!")
