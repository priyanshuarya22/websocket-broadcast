from fastapi import FastAPI, WebSocket, Cookie, WebSocketException, status
from starlette.websockets import WebSocketDisconnect
import asyncio
from datetime import datetime
from broadcaster import Broadcast
from pydantic import BaseModel
import contextlib


broadcast = Broadcast("redis://localhost:6379")
CHANNEL = "CHAT"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await broadcast.connect()
    yield
    await broadcast.disconnect()


app = FastAPI(lifespan=lifespan)


class MessageEvent(BaseModel):
    username: str
    message: str


async def recieve_message(websocket: WebSocket, username: str):
    async with broadcast.subscribe(channel=CHANNEL) as subscriber:
        async for event in subscriber:
            message_event = MessageEvent.parse_raw(event.message)
            if message_event.username != username:
                await websocket.send_json(message_event.dict())


async def send_message(websocket: WebSocket, username: str):
    data = await websocket.receive_text()
    event = MessageEvent(username=username, message=data)
    await broadcast.publish(channel=CHANNEL, message=event.json())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, username: str = "Anonymous"):
    await websocket.accept()
    try:
        while True:
            recieve_message_task = asyncio.create_task(recieve_message(websocket, username))
            send_message_task = asyncio.create_task(send_message(websocket, username))
            done, pending = await asyncio.wait({recieve_message_task, send_message_task}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
    except WebSocketDisconnect:
        pass
