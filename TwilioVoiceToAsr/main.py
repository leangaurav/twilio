import argparse
import asyncio
import base64
import json
import time
import weakref

import aiohttp
from aiohttp import web
from aiohttp import WSCloseCode
from utils import get_logger, set_google_creds_path
set_google_creds_path('token.json')

from google_asr import AsrConfig,AudioEncoding, AsrType, get_async_streaming_asr_client


LOGGER = get_logger()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind_address', required=True, type=str, help='an integer for the accumulator')
    parser.add_argument('--ws_host', required=True, type=str, help='public host address')
    #parser.add_argument('--max_call_time', type=int, default=30, help='Maximum time in seconds for call to run. -1 to disable')
    return parser.parse_args()


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    start_ts = time.time()

    LOGGER.info("connected")
    request.app["websockets"].add(ws)

    asr_config = AsrConfig(
        sample_rate=8000,
        encoding=AudioEncoding.MULAW,
        asr_type=AsrType.GOOGLE,
        language="en-US",
    )

    audio_pipe = AsyncIteratorPipe()
    print("connect start")
    asyncio.ensure_future(asr_loop(asr_config, audio_pipe))
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    event = json.loads(msg.data)
                    event_type = event.get("event")
                    if event_type == "start":
                        LOGGER.info(f"Got Start message: {event}")
                    elif event_type == "media":
                        payload = event.get("media", {}).get("payload", "")
                        if payload is None:
                            LOGGER.info("Missing audio payload in media event")
                        else:
                            LOGGER.info(f"Payload length: {len(payload)}")
                            await audio_pipe.put(base64.b64decode(payload))
                    elif event_type == "connected":
                        LOGGER.info(f"Got Connect message: {event}")
                    else:
                        LOGGER.info(f"Unknown message type: {event_type}")

                except Exception as err:
                    LOGGER.info(f"unable to process messaage {err}")
                    # await ws.send_json(response)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                LOGGER.error('ws connection closed with exception %s' %
                      ws.exception())
                break

    finally:
        await audio_pipe.close()
        request.app['websockets'].discard(ws)

    LOGGER.info("websocket closed")
    return ws

async def asr_loop(asr_config, audio_pipe):
    asr_results_iter = await get_async_streaming_asr_client(asr_config, audio_pipe)
    async for result in asr_results_iter:
        print('got result', result)


async def twiml_handler(request):
    LOGGER.info(f"Twiml headers {request.headers}")
    text  = await request.text()
    LOGGER.info(f"Twiml headers {text}")

    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>This is an echo bot </Say>
        <Connect>
           <Stream url="{WS_ADDRESS}/call" />
        </Connect>
    </Response>"""

    LOGGER.info(f"Returning Twiml: {twiml_response}")
    return web.Response(text=twiml_response, content_type='text/xml')

async def on_shutdown(app):
    for ws in set(app['websockets']):
        await ws.close(code=WSCloseCode.GOING_AWAY,
                       message='Server shutdown')

class AsyncIteratorPipe:

    def __init__(self, sentinel=object()):
        self._q = asyncio.Queue()
        self._sentinel = sentinel

    def __aiter__(self):
        return self

    async def __anext__(self):
        data = await self._q.get()
        if data is self._sentinel:
            raise StopAsyncIteration

        return data

    async def put(self, data):
        await self._q.put(data)

    async def close(self):
        await self._q.put(self._sentinel)

if __name__ == "__main__":

    args = parse_args()
    WS_ADDRESS = args.ws_host
    BIND_ADDRESS = args.bind_address
    #MAX_CALL_DURATION = args.max_call_time

    if WS_ADDRESS is None:
        LOGGER.error("Missing WS_ADDRESS:{WS_ADDRESS}")
        exit()
    if BIND_ADDRESS is None :
        LOGGER.error("Missing BIND_ADDRESS:{BIND_ADDRESS}")
        exit()

    host, port = BIND_ADDRESS.rsplit(":", 1)
    port = int(port)
    LOGGER.info(f"Running: host={host} port={port}")
    app = web.Application()
    app["websockets"] = weakref.WeakSet()
    app.on_shutdown.append(on_shutdown)

    app.add_routes([
            web.get("/call", websocket_handler),
            web.route("*", "/twiml", twiml_handler),
        ])
    web.run_app(app, host=host, port=port)
