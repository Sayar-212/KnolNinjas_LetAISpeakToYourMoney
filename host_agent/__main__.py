import httpx
from fastapi import FastAPI
import uvicorn

from server import ConversationServer
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    conv_server = ConversationServer(app=app, http_client=httpx.AsyncClient())
    await conv_server.manager._host_agent.get_addresses()
    yield


if __name__ == "__main__":
    app = FastAPI(lifespan=lifespan)
    uvicorn.run(app=app, host="0.0.0.0", port=8080)
