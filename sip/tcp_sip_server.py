import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from video_stream import CustomVideoStreamTrack
from sip_parser import parse_sip_message, build_200_ok_response

camera_id = 0
pcs = set()


class TCPProtocolImpl:
    def __init__(self, incoming_invite_handler):
        self.incoming_invite_handler = incoming_invite_handler

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connected to {addr}")

        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break

                message = data.decode()
                print(f"Received message from {addr}:\n{message}")
                headers, sdp_offer = parse_sip_message(message)

                if headers is not None and "invite" in headers["request-line"]:
                    sdp_answer = await self.incoming_invite_handler(sdp_offer)
                    response = build_200_ok_response(message, sdp_answer)
                    print(f"Sending response:\n{response}")
                    writer.write(response.encode())
                    await writer.drain()
        except asyncio.CancelledError:
            print(f"Connection closed with {addr}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def listen(self, host="0.0.0.0", port=5090):
        server = await asyncio.start_server(self.handle_client, host, port)
        addr = server.sockets[0].getsockname()
        print(f"TCP Server running on {addr}")
        async with server:
            await server.serve_forever()


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
    transport = TCPProtocolImpl(incoming_invite_handler=on_sip_invite)
    await transport.listen()

    # Periodically clean up closed peer connections
    def dummy_callback():
        pass
    cleanup_task = asyncio.create_task(cleanup_pcs())
    cleanup_task.add_done_callback(lambda t: dummy_callback)

    # keep loop
    while True:
        await asyncio.sleep(3600)


asyncio.run(main())