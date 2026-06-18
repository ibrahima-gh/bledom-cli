"""BLE connection manager with automatic reconnection. No OS-specific logic."""

import asyncio
import logging
from typing import Optional

from bleak import BleakClient, BleakScanner

from . import protocol, config

logger = logging.getLogger(__name__)

RECONNECT_DELAY = 5  # seconds between reconnection attempts


class BLEConnection:
    def __init__(self) -> None:
        self._client: Optional[BleakClient] = None
        self._address: Optional[str] = None
        self._connected = False
        self._reconnect_task: Optional[asyncio.Task] = None

    @property
    def connected(self) -> bool:
        return self._connected and self._client is not None and self._client.is_connected

    @property
    def address(self) -> Optional[str]:
        return self._address

    async def scan(self, timeout: float = 5.0) -> list[dict]:
        devices = await BleakScanner.discover(timeout=timeout)
        return [
            {"name": d.name, "address": d.address, "rssi": getattr(d, "rssi", None)}
            for d in devices
            if protocol.matches_device_name(d.name)
        ]

    async def connect(self, address: str) -> None:
        self._address = address
        config.set_value("device_address", address)
        await self._do_connect()
        if self.connected:
            self._start_reconnect_watcher()

    async def _do_connect(self) -> None:
        if self._address is None:
            return
        try:
            self._client = BleakClient(
                self._address,
                disconnected_callback=self._on_disconnect,
            )
            await self._client.connect()
            self._connected = True
            logger.info("Connected to %s", self._address)
        except Exception as e:
            self._connected = False
            logger.warning("Connection failed: %s", e)

    def _on_disconnect(self, client: BleakClient) -> None:
        self._connected = False
        logger.warning("Device disconnected, will retry in %ds", RECONNECT_DELAY)

    def _start_reconnect_watcher(self) -> None:
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        while True:
            await asyncio.sleep(RECONNECT_DELAY)
            if not self.connected and self._address:
                logger.info("Attempting reconnection to %s", self._address)
                try:
                    await self._do_connect()
                except Exception as e:
                    logger.warning("Reconnect attempt failed: %s", e)

    async def send(self, data: bytes) -> None:
        if not self.connected:
            raise RuntimeError("Not connected to any device")
        logger.debug("SEND → %s", data.hex(" "))
        await self._client.write_gatt_char(protocol.WRITE_UUID, data, response=False)

    async def power(self, on: bool) -> None:
        cfg = config.load()
        if on:
            # Restore last brightness then last color
            brightness = cfg.get("last_brightness") or 100
            c = cfg.get("last_color") or {"r": 255, "g": 255, "b": 255}
            await self.send(protocol.cmd_brightness(brightness))
            await asyncio.sleep(0.1)
            await self.send(protocol.cmd_color(c["r"], c["g"], c["b"]))
        else:
            await self.send(protocol.cmd_brightness(0))
        config.set_value("last_power", on)

    async def color(self, r: int, g: int, b: int) -> None:
        await self.send(protocol.cmd_color(r, g, b))
        config.set_value("last_color", {"r": r, "g": g, "b": b})

    async def brightness(self, value: int) -> None:
        await self.send(protocol.cmd_brightness(value))
        config.set_value("last_brightness", value)

    async def disconnect(self) -> None:
        if self._reconnect_task:
            self._reconnect_task.cancel()
        if self._client:
            await self._client.disconnect()
        self._connected = False
        self._address = None
        config.set_value("device_address", None)


# Singleton used by the API layer
ble = BLEConnection()
