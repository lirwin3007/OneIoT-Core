import json
import threading
from os import path
from subprocess import Popen

import oneiot_core.coreUtils.EventBus as EventBus
import oneiot_core.env as env

def verify_schedule_file(schedule):
    return isinstance(schedule, list) and all([verify_schedule_item(x) for x in schedule])

def verify_schedule_item(item):
    if not isinstance(item, dict):
        return False

    result = "id" in item
    result = result and "name" in item
    result = result and "entrypoint" in item
    result = result and "start_on_boot" in item

    if not result:
        return False

    result = isinstance(item['id'], str)
    result = result and isinstance(item["entrypoint"], list)
    result = result and isinstance(item["entrypoint"], list)
    result = result and isinstance(item["start_on_boot"], bool)

    if not result:
        return False

    for entrypointItem in item["entrypoint"]:
        if not isinstance(entrypointItem, str):
            return False

    return True

threads = {}

def run_process_in_thread(id, entrypoint, callback):
    process = Popen(entrypoint)
    res = process.wait()
    callback(id, res)
    return

uri = f'ws://0.0.0.0:{env.var("ONEIOT_C_PORT")}'
eventBus = EventBus.EventBus(uri)
eventBus.connect()

schedulePath = path.expanduser("~") + '/.oneIot/schedule.json'
if path.isfile(schedulePath):
    schedule = json.load(open(schedulePath))
else:
    schedule = []

if not verify_schedule_file(schedule):
    exit("Error in schedule.json")

def process_callback(processID, exitCode):
    eventBus.send('core.schedule.processExit', {
        'id': processID,
        'exit_code': exitCode
    })

for item in schedule:
    if item['start_on_boot']:
        threads[item['id']] = threading.Thread(target=run_process_in_thread, args=(item['id'], item['entrypoint'], process_callback))
        threads[item['id']].start()
        eventBus.send('core.schedule.processStart', {
            'id': item['id']
        })

#eventBus.disconnect()