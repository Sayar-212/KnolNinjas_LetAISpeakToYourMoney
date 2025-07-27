import httpx
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
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
    origins = [
        "http://localhost:5173",  # React/Vite dev server
        "http://127.0.0.1:5173",
        "https://your-frontend-domain.com",
        "*",  # ⚠️ Allow all origins (for development only)
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # List of allowed origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
        allow_headers=["*"],  # Allow all headers
    )
    uvicorn.run(app=app, host="0.0.0.0", port=8080)
