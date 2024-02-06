# Websocket Broadcast

A simple Broadcasting application which uses websockets to maintain a duplex connection, Redis as data broker and FastAPI for creating asynchronous APIs.

To run redis use the following command: `docker run -d --name fastapi-redis -p 6379:6379 redis`