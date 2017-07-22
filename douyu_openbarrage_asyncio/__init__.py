import asyncio
import time

from douyu_openbarrage_asyncio import douyu_packet
from douyu_openbarrage_asyncio import douyu_datastructure

BUF_SIZE=8192

class DouyuClient():
    @classmethod
    async def create(cls,future,roomid,on_message_event_handler,inner_loop_exception_event_handler=None,outter_loop_exception_event_handler=None):
        self = cls()
        self.roomid = roomid
        self.on_message_event_handler = on_message_event_handler
        self.inner_loop_exception_event_handler = inner_loop_exception_event_handler
        self.outter_loop_exception_event_handler = outter_loop_exception_event_handler
        await self.handshake()
        future.set_result(self)

    async def heartbeat(self,duration=30):
        while True:
            try:
                msg = douyu_datastructure.serialize({'type': 'keepalive', 'tick':int(time.time())})
                self.writer.write(douyu_packet.to_raw(msg))
                await self.writer.drain()
                await asyncio.sleep(duration)
            except Exception as inst:
                if self.outter_loop_exception_event_handler is not None:
                    await self.outter_loop_exception_event_handler(inst)
                await self.handshake()

    async def handshake(self):
        self.reader, self.writer = await asyncio.open_connection('openbarrage.douyutv.com', 8601)
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
                content,remains = douyu_packet.from_raw(await self.reader.read(BUF_SIZE), remains)
                for item in content:
                    try:
                        msg = douyu_datastructure.deserialize(item.decode('utf-8'))
                        await self.on_message_event_handler(msg)
                    except Exception as inst:
                        if self.inner_loop_exception_event_handler is not None:
                            await self.inner_loop_exception_event_handler(inst)
            except Exception as inst:
                if self.outter_loop_exception_event_handler is not None:
                    await self.outter_loop_exception_event_handler(inst)
                await self.handshake()

    async def main(self):
        asyncio.ensure_future(self.mainloop())
        asyncio.ensure_future(self.heartbeat())

def DouyuFactorty(roomid,on_message_event_handler,inner_loop_exception_event_handler=None,outter_loop_exception_event_handler=None):
    loop = asyncio.get_event_loop()
    future = asyncio.Future()
    asyncio.ensure_future(DouyuClient.create(future, roomid, on_message_event_handler,inner_loop_exception_event_handler,outter_loop_exception_event_handler))
    loop.run_until_complete(future)
    ins = future.result()
    asyncio.ensure_future(ins.main())