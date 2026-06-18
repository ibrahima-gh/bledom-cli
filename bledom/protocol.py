"""
ELK-BLEDOM / BLEDOM protocol implementation.

Write characteristic: 0000fff3-0000-1000-8000-00805f9b34fb
Notify characteristic: 0000fff4-0000-1000-8000-00805f9b34fb

Power is implemented via brightness (0 = off, restore = on) because
the hardware toggle command is stateless and unreliable.
"""

WRITE_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

DEVICE_NAME_PATTERNS = [
    "bledom",
    "elk-ble",
    "melk",
    "ledble",
    "bleddm",
    "elk_ble",
]


def cmd_color(r: int, g: int, b: int) -> bytes:
    r, g, b = _clamp(r), _clamp(g), _clamp(b)
    return bytes([0x7E, 0x00, 0x05, 0x03, r, g, b, 0x00, 0xEF])


def cmd_brightness(value: int) -> bytes:
    """value: 0-100. Send 0 to power off, restore last value to power on."""
    v = max(0, min(100, value))
    return bytes([0x7E, 0x00, 0x01, v, 0x00, 0x00, 0x00, 0xFF, 0xEF])


def _clamp(v: int) -> int:
    return max(0, min(255, v))


def matches_device_name(name: "str | None") -> bool:
    if not name:
        return False
    lower = name.lower()
    return any(p in lower for p in DEVICE_NAME_PATTERNS)
