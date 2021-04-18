import argparse
import asyncio
import json
import  os
import time
import weakref
from dataclasses import dataclass

import aiohttp
from aiohttp import web
from aiohttp import WSCloseCode

from utils import get_logger

LOGGER = get_logger()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind_address', required=True, type=str, help='an integer for the accumulator')
    parser.add_argument('--ws_host', required=True, type=str, help='public host address')
    parser.add_argument('--max_call_time', type=int, default=30, help='Maximum time in seconds for call to run. -1 to disable')
    return parser.parse_args()

def process_message(msg: str):
    try:
        event = json.loads(msg)
        event_type = event.get("event")
        if event_type == "start":
            return process_start(event)
        elif event_type == "media":
            return process_media(event)
        elif event_type == "connected":
            return process_connect(event)
        else:
            LOGGER.info(f"Unknown message type: {event_type}")

    except Exception as err:
        LOGGER.info(f"unable to process messaage {err}")

    return None

def process_start(event):
    LOGGER.info(f"Got Start message: {event}")

def process_media(event):
    sid =  event.get("streamSid")
    if  sid is None:
        LOGGER.info("Missing stream id in media event")
        return

    payload = event.get("media",{}).get("payload", "")
    if payload is None:
        LOGGER.info("Missing audio payload in media event")
        return
    else:
        LOGGER.info(f"Payload length: {len(payload)}")

    return {
        "event": "media",
        "media": {
            "payload": payload,
        },
        "streamSid": sid,
    }

def process_connect(event):
    LOGGER.info(f"Got Connect message: {event}")

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    start_ts = time.time()

    LOGGER.info("connected")
    request.app["websockets"].add(ws)
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                response = process_message(msg.data)
                if  response is not None:
                    await ws.send_json(response)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                LOGGER.error('ws connection closed with exception %s' %
                      ws.exception())
                break

            if MAX_CALL_DURATION != -1 and time.time() - start_ts >= MAX_CALL_DURATION:
                break
    finally:
        request.app['websockets'].discard(ws)

    LOGGER.info("websocket closed")
    return ws

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

if __name__ == "__main__":

    args = parse_args()
    WS_ADDRESS = args.ws_host
    BIND_ADDRESS = args.bind_address
    MAX_CALL_DURATION = args.max_call_time

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
