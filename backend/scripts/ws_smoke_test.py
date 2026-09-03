"""Minimal WebSocket smoke test for the Hermes web gateway.

Connects to ws://localhost:8000/ws, performs the JSON-RPC handshake
(session.create -> message.send), and prints the streamed events plus the
reassembled mock reply. Intended as a manual/CI smoke check of the gateway.
"""

from __future__ import annotations

import asyncio
import json

import websockets

WS_URL = "ws://localhost:8000/ws"


async def main() -> None:
    async with websockets.connect(WS_URL) as ws:
        print(f"[connected] {WS_URL}")

        create_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "session.create",
            "params": {"session_key": "smoke-test"},
        }
        await ws.send(json.dumps(create_req))
        create_resp = json.loads(await ws.recv())
        print(f"[session.create response] {json.dumps(create_resp)}")
        session_id = create_resp["result"]["session_id"]

        send_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "message.send",
            "params": {"session_id": session_id, "text": "Hello Hermes from the smoke test!"},
        }
        await ws.send(json.dumps(send_req))

        deltas: list[str] = []
        final_ack: dict | None = None
        while True:
            msg = json.loads(await ws.recv())
            method = msg.get("method")
            if method == "event":
                etype = msg["params"]["type"]
                payload = msg["params"].get("payload", {})
                if etype == "message.start":
                    print(f"[event] message.start session={payload.get('session_id')}")
                elif etype == "message.delta":
                    chunk = payload.get("text", "")
                    deltas.append(chunk)
                    print(f"[event] message.delta -> {chunk!r}")
                elif etype == "message.complete":
                    print(f"[event] message.complete session={payload.get('session_id')}")
                    break
            elif msg.get("id") == 2:
                final_ack = msg

        # message.send RPC ack may arrive interleaved; read it if not seen yet.
        if final_ack is None:
            try:
                final_ack = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
            except asyncio.TimeoutError:
                final_ack = None

        reply = "".join(deltas)
        print("-" * 50)
        print(f"[reassembled mock reply] {reply!r}")
        if final_ack is not None:
            print(f"[message.send ack] {json.dumps(final_ack)}")
        assert reply.startswith("[Mock Hermes] Received:"), "unexpected mock reply"
        print("[PASS] WebSocket streaming handshake succeeded.")


if __name__ == "__main__":
    asyncio.run(main())
