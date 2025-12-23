# server.py
import asyncio
import json
import logging
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack, RTCIceCandidate
from aiortc.contrib.media import MediaRelay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webrtc-server")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory mapping: call_key -> list of PeerConnections
CALL_PCS: Dict[str, List[RTCPeerConnection]] = {}
RELAY = MediaRelay()

class Offer(BaseModel):
    call_key: str
    sdp: str
    type: str

class Candidate(BaseModel):
    call_key: str
    candidate: dict  # candidate dict as sent by browser

# helper to cleanup
async def close_pc(pc: RTCPeerConnection):
    try:
        await pc.close()
    except Exception:
        pass

# server.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep track of connected clients by call_key
connections: Dict[str, List[WebSocket]] = {}

@app.websocket("/ws/{call_key}")
async def websocket_endpoint(websocket: WebSocket, call_key: str):
    await websocket.accept()
    if call_key not in connections:
        connections[call_key] = []
    connections[call_key].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            # broadcast the data to other clients in the same call
            for conn in connections[call_key]:
                if conn != websocket:
                    await conn.send_json(data)
    except Exception:
        pass
    finally:
        connections[call_key].remove(websocket)
        if not connections[call_key]:
            del connections[call_key]

@app.post("/offer")
async def offer(offer: Offer):
    """
    Receive SDP offer from browser, create aiortc RTCPeerConnection,
    set remote description, create answer and return.
    Also attach on_track handler to forward incoming audio to other PCs in same call_key.
    """
    call_key = offer.call_key
    logger.info("Offer received for call_key=%s", call_key)

    pc = RTCPeerConnection()
    pc_id = id(pc)
    logger.info("Created PC %s for call %s", pc_id, call_key)

    # ensure list exists
    pcs = CALL_PCS.setdefault(call_key, [])
    pcs.append(pc)

    @pc.on("iceconnectionstatechange")
    async def on_ice_state():
        logger.info("pc %s ICE %s", pc_id, pc.iceConnectionState)
        if pc.iceConnectionState == "failed" or pc.iceConnectionState == "closed":
            # cleanup
            if pc in CALL_PCS.get(call_key, []):
                CALL_PCS[call_key].remove(pc)
            await close_pc(pc)

    # When a remote track arrives on this pc,
    # forward it to all other PCs in the same call_key
    @pc.on("track")
    def on_track(track: MediaStreamTrack):
        logger.info("pc %s received track %s kind=%s", pc_id, track.kind, track.kind)
        if track.kind == "audio":
            # use relay to subscribe safely
            relayed = RELAY.subscribe(track)

            # add this relayed track to each other pc in the call
            for other in list(CALL_PCS.get(call_key, [])):
                if other is pc:
                    continue
                try:
                    other.addTrack(relayed)
                    logger.info("Added relayed audio track to pc %s (from pc %s)", id(other), pc_id)
                except Exception as e:
                    logger.exception("Failed to add track to pc %s: %s", id(other), e)

        @track.on("ended")
        async def on_ended():
            logger.info("Track ended on pc %s", pc_id)

    # set remote description
    remote_desc = RTCSessionDescription(sdp=offer.sdp, type=offer.type)
    await pc.setRemoteDescription(remote_desc)

    # create answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # return answer (sdp + type)
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

@app.post("/candidate")
async def add_candidate(cand: Candidate):
    """
    Add incoming ICE candidate from browser to all pcs for this call_key.
    The browser should send {'call_key': ..., 'candidate': candidateObject}
    """
    call_key = cand.call_key
    candidate = cand.candidate
    pcs = CALL_PCS.get(call_key, [])
    if not pcs:
        raise HTTPException(status_code=404, detail="Call not found")
    # For simplicity, add candidate to the most-recent pc (caller) — you can choose better routing.
    # Here we add candidate to ALL pcs in the call; aiortc will ignore duplicates.
    for pc in pcs:
        try:
            ice = RTCIceCandidate(
                sdpMid=candidate.get("sdpMid"),
                sdpMLineIndex=candidate.get("sdpMLineIndex"),
                candidate=candidate.get("candidate"),
            )
            # aiortc expects addIceCandidate called in event loop
            coro = pc.addIceCandidate(ice)
            if asyncio.iscoroutine(coro):
                await coro
        except Exception as e:
            logger.exception("Failed to add candidate to pc %s: %s", id(pc), e)
    return {"ok": True}

@app.post("/hangup")
async def hangup(request: Request):
    """
    Hangup: remove and close all pcs for a call_key passed in JSON body.
    """
    body = await request.json()
    call_key = body.get("call_key")
    if not call_key:
        raise HTTPException(status_code=400, detail="call_key required")
    pcs = CALL_PCS.pop(call_key, [])
    for pc in pcs:
        await close_pc(pc)
    return {"ok": True}
