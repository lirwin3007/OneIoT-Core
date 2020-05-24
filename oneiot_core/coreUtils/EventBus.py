import json
import asyncio
import threading

import websockets


class EventBus():

    def __init__(self, uri):
        self.uri = uri

        self.loop = asyncio.new_event_loop()
        # Create a queue of user inputs. There's no need to limit its size.
        self.inputs = asyncio.Queue(loop=self.loop)

        # Create a stop condition
        self.stop = self.loop.create_future()


    def connect(self):
        # Create an event loop that will run in a background thread.
        
        # Schedule the task that will manage the connection.
        asyncio.ensure_future(self.run_client(self.loop), loop=self.loop)

        # Start the event loop in a background thread.
        self.thread = threading.Thread(target=self.loop.run_forever)
        self.thread.start()
        
    def disconnect(self):
        self.loop.call_soon_threadsafe(self.stop.set_result, None)

        # Wait for the event loop to terminate.
        self.thread.join()

    async def run_client(self, loop):
        # Initiate the connection
        try:
            websocket = await websockets.connect(self.uri)
        except Exception as exc:
            # Probably should throw an error here
            return

        # Main loop
        try:
            while True:
                # Execute the incoming and outgoing tasks
                incoming = asyncio.ensure_future(websocket.recv())
                outgoing = asyncio.ensure_future(self.inputs.get())
                done, pending = await asyncio.wait([incoming, outgoing, self.stop], return_when=asyncio.FIRST_COMPLETED)

                # Cancel pending tasks to avoid leaking them.
                if incoming in pending:
                    incoming.cancel()
                if outgoing in pending:
                    outgoing.cancel()

                # Take action on the tasks
                # Incoming tasks
                if incoming in done:
                    message = incoming.result()
                    await self.consumer_handler(message)

                # Outgoing tasks
                if outgoing in done:
                    message = outgoing.result()
                    await websocket.send(message)
                    
                # Stop task
                if self.stop in done:
                    break

        finally:
            # Close the socket and running loop
            await websocket.close()
            asyncio.get_running_loop().stop()

    async def consumer_handler(self, message):
        print(message)

    def send(self, id, data):
        message = json.dumps({
            'id': id,
            'data': data
        })
        self.loop.call_soon_threadsafe(self.inputs.put_nowait, message)


# a = EventBus("ws://192.168.2.111:1104")
# a.connect()
# a.send('hello.world', True)
# a.disconnect()
