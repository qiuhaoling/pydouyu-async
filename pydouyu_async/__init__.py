import asyncio
import time

from . import douyu_datastructure
from . import douyu_packet

BUF_SIZE = 4096
DOUYU_HOST='openbarrage.douyutv.com'
DOUYU_PORT=8601
class DouyuClient():
    def __init__(self,roomid,on_message_event_handler,inner_loop_exception_event_handler=None,outter_loop_exception_event_handler=None):
        super().__init__()
        self.roomid = roomid
        self.on_message_event_handler = on_message_event_handler
        self.inner_loop_exception_event_handler = inner_loop_exception_event_handler
        self.outter_loop_exception_event_handler = outter_loop_exception_event_handler
        self.message_in_past_duration = 1
        self.heartbeat_future = None
        self.mainloop_future = None
        self.reader = None
        self.writer = None
        self.handshake_lock = asyncio.Lock()
        asyncio.ensure_future(self.handshake())


    async def heartbeat(self,duration=30):
        while True:
            try:
                if self.message_in_past_duration < 1:
                    raise ConnectionError(
                        "[{}]No message received in the past {} seconds, reconnecting...".format(self.roomid, duration))
                msg = douyu_datastructure.serialize({'type': 'keepalive', 'tick':int(time.time())})
                self.writer.write(douyu_packet.to_raw(msg))
                await self.writer.drain()
                self.message_in_past_duration = 0
                await asyncio.sleep(duration)
            except asyncio.CancelledError:
                break
            except Exception as inst:
                if not self.handshake_lock.locked():
                    if self.outter_loop_exception_event_handler is not None:
                        await self.outter_loop_exception_event_handler(inst)
                    asyncio.ensure_future(self.handshake())
                await asyncio.sleep(0)

    async def cancel(self):
        with await self.handshake_lock:
            try:
                if self.heartbeat_future is not None:
                    self.heartbeat_future.cancel()
            except Exception as inst:
                if self.outter_loop_exception_event_handler is not None:
                    await self.outter_loop_exception_event_handler(inst)
            try:
                if self.mainloop_future is not None:
                    self.mainloop_future.cancel()
            except Exception as inst:
                if self.outter_loop_exception_event_handler is not None:
                    await self.outter_loop_exception_event_handler(inst)
            try:
                if self.writer is not None:
                    self.writer.close()
            except Exception as inst:
                if self.outter_loop_exception_event_handler is not None:
                    await self.outter_loop_exception_event_handler(inst)

    async def handshake(self):
        self.message_in_past_duration = 1
        await self.cancel()
        with await self.handshake_lock:
            try:
                self.reader, self.writer = await asyncio.open_connection(DOUYU_HOST, DOUYU_PORT)
                msg = douyu_datastructure.serialize({'type': 'loginreq', 'roomid': self.roomid})
                self.writer.write(douyu_packet.to_raw(msg))
                await self.writer.drain()
                msg = douyu_datastructure.serialize({'type': 'joingroup', 'rid': self.roomid, 'gid': -9999})
                self.writer.write(douyu_packet.to_raw(msg))
                await self.writer.drain()
                await self.main()
            except Exception as inst:
                if self.outter_loop_exception_event_handler is not None:
                    await self.outter_loop_exception_event_handler(inst)
                await asyncio.sleep(0)
                asyncio.ensure_future(self.handshake())

    async def mainloop(self):
        remains = None
        while True:
            try:
                if self.reader.at_eof():
                    raise Exception("[{}]Reader is invalid!".format(self.roomid))
                content, remains = douyu_packet.from_raw(await self.reader.read(BUF_SIZE), remains)
                for item in content:
                    try:
                        msg = douyu_datastructure.deserialize(item.decode('utf-8'))
                        if msg.get('type', None) == 'chatmsg':
                            self.message_in_past_duration += 1
                        await self.on_message_event_handler(msg)
                    except Exception as inst:
                        if self.inner_loop_exception_event_handler is not None:
                            await self.inner_loop_exception_event_handler(inst)
            except asyncio.CancelledError:
                break
            except Exception as inst:
                if not self.handshake_lock.locked():
                    if self.outter_loop_exception_event_handler is not None:
                        await self.outter_loop_exception_event_handler(inst)
                    asyncio.ensure_future(self.handshake())
                await asyncio.sleep(0)

    async def main(self):
        self.mainloop_future = asyncio.ensure_future(self.mainloop())
        self.heartbeat_future = asyncio.ensure_future(self.heartbeat())
