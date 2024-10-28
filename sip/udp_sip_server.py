import asyncio
from typing import Callable, Coroutine
from aiortc import RTCPeerConnection, RTCSessionDescription
from video_stream import CustomVideoStreamTrack
from sip_parser import parse_sip_message, build_200_ok_response

camera_id = 0
pcs = set()


class UDPProtocolImpl(asyncio.DatagramProtocol):
    def __init__(self, incoming_invite_handler):
        self.transport = None
        self.incoming_invite_handler = incoming_invite_handler

    def connection_made(self, transport):
        self.transport = transport
        server_addr = self.transport.get_extra_info('sockname')
        print(f"Server is up and running {server_addr}")

    def datagram_received(self, data, addr):
        message = data.decode()
        print(f"Received message from {addr}:\n{message}")
        headers, sdp_offer = parse_sip_message(message)

        if headers is not None and "invite" in headers["request-line"]:
            def callback(sdp_answer):
                response = build_200_ok_response(message, sdp_answer)
                print(f"Sending response:\n{response}")
                self.transport.sendto(response.encode(), addr)
            task = asyncio.create_task(self.incoming_invite_handler(sdp_offer))
            task.add_done_callback(lambda t: callback)
            return

    def error_received(self, exc):
        print(f"Error received: {exc}")

    def connection_lost(self, exc):
        print("Connection closed")


async def create_sdp_answer(sdp):
    offer = RTCSessionDescription(sdp=sdp, type="offer")

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # Add webcam video track to the peer connection
    video_track = CustomVideoStreamTrack(camera_id)
    pc.addTrack(video_track)

    # Set remote description and create answer
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return pc.localDescription.sdp


async def cleanup_pcs():
    while True:
        await asyncio.sleep(10)
        for pc in set(pcs):
            if pc.iceConnectionState == "closed":
                pcs.discard(pc)


async def on_sip_invite(sdp_offer: str):
    sdp_answer = await create_sdp_answer(sdp_offer)
    return sdp_answer


async def main():
    loop = asyncio.get_running_loop()

    print("Starting UDP server...")
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPProtocolImpl(incoming_invite_handler=on_sip_invite),
        local_addr=("0.0.0.0", 5090)
    )

    while True:
        try:
            await asyncio.sleep(3600)
        finally:
            transport.close()


asyncio.run(main())
