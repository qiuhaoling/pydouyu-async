import asyncio
import time

from douyu_openbarrage_asyncio import douyu_packet

from douyu_openbarrage_asyncio import douyu_datastructure


class DouyuClient():
    @classmethod
    async def create(cls,future,roomid,event_handler):
        self = cls()
        self.roomid = roomid
        self.event_handler = event_handler
        self.reader,self.writer = await asyncio.open_connection('openbarrage.douyutv.com',8601)
        await self.handshake(roomid)
        future.set_result(self)

    async def heartbeat(self,duration=30):
        while True:
            msg = douyu_datastructure.serialize({'type': 'keepalive', 'tick':int(time.time())})
            self.writer.write(douyu_packet.to_raw(msg))
            await self.writer.drain()
            await asyncio.sleep(duration)
    async def handshake(self,roomid):
        msg = douyu_datastructure.serialize({'type': 'loginreq', 'roomid':self.roomid})
        self.writer.write(douyu_packet.to_raw(msg))
        await self.writer.drain()
        content, remains = douyu_packet.from_raw(await self.reader.read(9999), None)
        msg = douyu_datastructure.serialize({'type': 'joingroup', 'rid':self.roomid, 'gid':-9999})
        self.writer.write(douyu_packet.to_raw(msg))
        await self.writer.drain()
    async def mainloop(self):
        remains = None
        while True:
            content,remains = douyu_packet.from_raw(await self.reader.read(9999), remains)
            for item in content:
                try:
                    msg = douyu_datastructure.deserialize(item.decode('utf-8'))
                    await self.event_handler(msg)
                except Exception as inst:
                    import traceback
                    traceback.print_exc()

    async def main(self):
        asyncio.ensure_future(self.mainloop())
        asyncio.ensure_future(self.heartbeat())

def DouyuFactorty(roomid,event_handler):
    loop = asyncio.get_event_loop()
    future = asyncio.Future()
    asyncio.ensure_future(DouyuClient.create(future, roomid, event_handler))
    loop.run_until_complete(future)
    ins = future.result()
    asyncio.ensure_future(ins.main())