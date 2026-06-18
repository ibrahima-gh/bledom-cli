"""FastAPI routes. No OS-specific logic."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .connection import ble

import logging
import pathlib

logger = logging.getLogger(__name__)

STATIC_DIR = pathlib.Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-connect to last known device on startup
    address = config.get("device_address")
    if address:
        logger.info("Auto-connecting to saved device %s", address)
        await ble.connect(address)
    yield
    await ble.disconnect()


app = FastAPI(title="bledom-cli", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Request models ---

class ConnectRequest(BaseModel):
    address: str

class PowerRequest(BaseModel):
    on: bool

class ColorRequest(BaseModel):
    r: int = Field(..., ge=0, le=255)
    g: int = Field(..., ge=0, le=255)
    b: int = Field(..., ge=0, le=255)

class BrightnessRequest(BaseModel):
    value: int = Field(..., ge=0, le=100)


# --- Routes ---

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/scan")
async def scan(timeout: float = 5.0):
    devices = await ble.scan(timeout=timeout)
    return {"devices": devices}


@app.post("/connect")
async def connect(req: ConnectRequest):
    await ble.connect(req.address)
    if not ble.connected:
        raise HTTPException(status_code=502, detail="Could not connect to device")
    return {"status": "connected", "address": req.address}


@app.get("/status")
async def status():
    cfg = config.load()
    return {
        "connected": ble.connected,
        "reconnecting": not ble.connected and ble.address is not None,
        "address": ble.address,
        "last_color": cfg.get("last_color"),
        "last_brightness": cfg.get("last_brightness"),
        "last_power": cfg.get("last_power"),
    }


@app.post("/power")
async def power(req: PowerRequest):
    _require_connection()
    await ble.power(req.on)
    return {"power": req.on}


@app.post("/color")
async def color(req: ColorRequest):
    _require_connection()
    await ble.color(req.r, req.g, req.b)
    return {"color": {"r": req.r, "g": req.g, "b": req.b}}


@app.post("/brightness")
async def brightness(req: BrightnessRequest):
    _require_connection()
    await ble.brightness(req.value)
    return {"brightness": req.value}


class RawRequest(BaseModel):
    hex: str  # ex: "7e 00 04 f0 00 01 ff 00 ef"

@app.post("/send_raw")
async def send_raw(req: RawRequest):
    _require_connection()
    data = bytes.fromhex(req.hex.replace(" ", ""))
    await ble.send(data)
    return {"sent": req.hex}


@app.get("/inspect")
async def inspect():
    _require_connection()
    result = []
    for service in ble._client.services:
        for ch in service.characteristics:
            result.append({
                "service": service.uuid,
                "characteristic": ch.uuid,
                "properties": ch.properties,
                "description": ch.description,
            })
    return {"characteristics": result}


@app.post("/disconnect")
async def disconnect():
    await ble.disconnect()
    return {"status": "disconnected"}


def _require_connection():
    if not ble.connected:
        raise HTTPException(status_code=503, detail="Not connected to any BLE device")
