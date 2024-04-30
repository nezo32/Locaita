import json
import tornado.web
import tornado.websocket
import tornado.ioloop
from constants import GOSU_WEBSOCKET_URL, THREAD_CLOSE_EVENT

async def OsuClient():
    return await tornado.websocket.websocket_connect(GOSU_WEBSOCKET_URL)

async def GetState(client):
    response = await client.read_message()
    return json.loads(response)