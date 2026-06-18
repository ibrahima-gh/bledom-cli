"""
ELK-BLEDOM / BLEDOM protocol implementation.

Command bytes sourced from:
  - HA integration led_ble (https://github.com/Bluetooth-Devices/led-ble)
  - Custom component zengge (https://github.com/8none1/zengge_lednetwf)

Write characteristic UUID used by ELK-BLEDOM devices:
  0000fff3-0000-1000-8000-00805f9b34fb  (write without response)

Notification characteristic:
  0000fff4-0000-1000-8000-00805f9b34fb

If your device uses different UUIDs, run a scan with --verbose and inspect
the service/characteristic list, then update WRITE_UUID below.
"""

WRITE_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

# Device name patterns for discovery (case-insensitive substring match)
DEVICE_NAME_PATTERNS = [
    "bledom",
    "elk-ble",
    "melk",
    "ledble",
    "bleddm",
    "elk_ble",
]


def cmd_power(on: bool) -> bytes:
    if on:
        return bytes([0x7E, 0x00, 0x04, 0xF0, 0x00, 0x01, 0xFF, 0x00, 0xEF])
    return bytes([0x7E, 0x00, 0x04, 0xF0, 0x00, 0x00, 0xFF, 0x00, 0xEF])


def cmd_color(r: int, g: int, b: int) -> bytes:
    r, g, b = _clamp(r), _clamp(g), _clamp(b)
    return bytes([0x7E, 0x00, 0x05, 0x03, r, g, b, 0x00, 0xEF])


def cmd_brightness(value: int) -> bytes:
    """value: 0-100 → mapped to 0x00-0x64"""
    v = max(0, min(100, value))
    return bytes([0x7E, 0x00, 0x01, v, 0x00, 0x00, 0x00, 0xFF, 0xEF])


def _clamp(v: int) -> int:
    return max(0, min(255, v))


def matches_device_name(name: str | None) -> bool:
    if not name:
        return False
    lower = name.lower()
    return any(p in lower for p in DEVICE_NAME_PATTERNS)
