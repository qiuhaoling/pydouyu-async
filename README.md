# douyu
pydouyu project rewritten using asyncio

Original credit for [yingnansong/pydouyu](https://github.com/yingnansong/pydouyu)

The only dependency is Python 3.5.

# basic usage
```
import asyncio
from pydouyu_async import DouyuClient

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    async def event_handler(msg):
        if msg.get('type',None) == 'chatmsg':
            print(msg)
    DouyuClient(507882,event_handler) #zyt820
    DouyuClient(74960,event_handler) #achuan
    DouyuClient(20360,event_handler) #lengleng
    DouyuClient(339610,event_handler) #danche
    DouyuClient(58718,event_handler) #Chuan
    DouyuClient(58428,event_handler) #yyf

    loop.run_forever()
```