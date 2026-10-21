"""
StreamBatch - Native Messaging Host for Chrome / Edge / Brave
Listens for messages from the browser extension via standard I/O (binary length prefix)
and routes them to the StreamBatch desktop application.
"""
import sys
import json
import struct
import urllib.request
import urllib.error

LOCAL_API_URL = "http://127.0.0.1:9654/add"

def send_native_response(message_dict):
    """Encodes response dictionary as 32-bit length-prefixed UTF-8 JSON."""
    encoded = json.dumps(message_dict).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()

def read_native_message():
    """Reads 32-bit length-prefixed UTF-8 JSON message from stdin."""
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length or len(raw_length) < 4:
        return None
    message_length = struct.unpack("I", raw_length)[0]
    message_bytes = sys.stdin.buffer.read(message_length)
    return json.loads(message_bytes.decode("utf-8"))

def main():
    while True:
        try:
            msg = read_native_message()
            if msg is None:
                break

            action = msg.get("action")
            url = msg.get("url")
            fmt = msg.get("format", "mp3")
            quality = msg.get("quality", "320")

            if action == "add_download" and url:
                # Forward to desktop application local loopback API
                payload = json.dumps({"url": url, "format": fmt, "quality": quality}).encode("utf-8")
                req = urllib.request.Request(
                    LOCAL_API_URL,
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                try:
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        res_data = json.loads(resp.read().decode("utf-8"))
                        send_native_response({"status": "success", "desktop_response": res_data})
                except Exception as e:
                    send_native_response({"status": "error", "error": f"StreamBatch is not running: {e}"})
            else:
                send_native_response({"status": "error", "error": "Unknown action or missing url"})

        except Exception as e:
            send_native_response({"status": "error", "error": str(e)})
            break

if __name__ == "__main__":
    main()
