from .websocket import FFmpegSinkFD
from ..dependencies import websockets


class FMPlaPlaFD(FFmpegSinkFD):
    async def real_connection(self, sink, info_dict):
        async with websockets.connect(info_dict['url'], subprotocols=['listener.fmplapla.com'],
                                      extra_headers=info_dict.get('http_headers', {})) as ws:
            await ws.send(info_dict.get('token'))
            while True:
                recv = await ws.recv()
                if isinstance(recv, str):
                    recv = recv.encode('utf8')
                sink.write(recv)
