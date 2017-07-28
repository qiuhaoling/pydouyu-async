import asyncio
import time

from . import douyu_datastructure
from . import douyu_packet

BUF_SIZE=8192
DOUYU_HOST='openbarrage.douyutv.com'
DOUYU_PORT=8601

class DouyuClient():
    def __init__(self,roomid,on_message_event_handler,inner_loop_exception_event_handler=None,outter_loop_exception_event_handler=None):
        super().__init__()
        self.roomid = roomid
        self.on_message_event_handler = on_message_event_handler
        self.inner_loop_exception_event_handler = inner_loop_exception_event_handler
        self.outter_loop_exception_event_handler = outter_loop_exception_event_handler
        loop = asyncio.get_event_loop()
        self.message_in_past_duration = 1
        self.message_in_past_duration_lock = asyncio.Lock()
        self.io_lock = asyncio.Lock()
        loop.run_until_complete(self.handshake())
        asyncio.ensure_future(self.main())


    async def heartbeat(self,duration=30):
        while True:
            try:
                if self.message_in_past_duration < 1:
                    raise Exception("[{}]No message received in the past {} seconds, reconnecting...".format(self.roomid,duration))
                msg = douyu_datastructure.serialize({'type': 'keepalive', 'tick':int(time.time())})
                with await self.io_lock:
                    self.writer.write(douyu_packet.to_raw(msg))
                    await self.writer.drain()
                with await self.message_in_past_duration_lock:
                    self.message_in_past_duration = 0
                await asyncio.sleep(duration)
            except Exception as inst:
                if self.outter_loop_exception_event_handler is not None:
                    await self.outter_loop_exception_event_handler(inst)
                await self.handshake()

    async def handshake(self):
        with await self.message_in_past_duration_lock:
            self.message_in_past_duration = 1
        with await self.io_lock:
            try:
                self.reader.close()
            except:
                pass
            try:
                self.writer.close()
            except:
                pass
            self.reader, self.writer = await asyncio.open_connection(DOUYU_HOST, DOUYU_PORT)
            msg = douyu_datastructure.serialize({'type': 'loginreq', 'roomid':self.roomid})
            self.writer.write(douyu_packet.to_raw(msg))
            await self.writer.drain()
            msg = douyu_datastructure.serialize({'type': 'joingroup', 'rid':self.roomid, 'gid':-9999})
            self.writer.write(douyu_packet.to_raw(msg))
            await self.writer.drain()

    async def mainloop(self):
        remains = None
        while True:
            try:
                if self.reader.at_eof():
                    await self.handshake()
                with await self.io_lock:
                    content,remains = douyu_packet.from_raw(await self.reader.read(BUF_SIZE), remains)
                for item in content:
                    with await self.message_in_past_duration_lock:
                        self.message_in_past_duration += 1
                    try:
                        msg = douyu_datastructure.deserialize(item.decode('utf-8'))
                        await self.on_message_event_handler(msg)
                    except Exception as inst:
                        if self.inner_loop_exception_event_handler is not None:
                            await self.inner_loop_exception_event_handler(inst)
            except Exception as inst:
                if self.outter_loop_exception_event_handler is not None:
                    await self.outter_loop_exception_event_handler(inst)

    async def main(self):
        asyncio.ensure_future(self.mainloop())
        asyncio.ensure_future(self.heartbeat())

def DouyuFactorty(roomid,on_message_event_handler,inner_loop_exception_event_handler=None,outter_loop_exception_event_handler=None):
    DouyuClient(roomid, on_message_event_handler,inner_loop_exception_event_handler,outter_loop_exception_event_handler)