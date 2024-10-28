import asyncio
import textwrap
from asyncio import DatagramTransport


class MyDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport: DatagramTransport = None

    def connection_made(self, transport: DatagramTransport):
        self.transport = transport
        print(f"Sending: {self.message}")
        self.transport.sendto(self.message.encode())

    def datagram_received(self, data, addr):
        print(f"Received: {data.decode()} from {addr}")
        self.transport.close()

    def error_received(self, exc):
        print(f"Error received: {exc}")

    def connection_lost(self, exc):
        print("Connection closed")
        self.on_con_lost.set_result(True)


async def udp_client():
    message = ("INVITE sip:user@example.com SIP/2.0\r\n"
               "Via: SIP/2.0/UDP pc33.example.com;branch=z9hG4bK776asdhds\r\n"
               "Max-Forwards: 70\r\n"
               "To: <sip:user@example.com>\r\n"
               "From: \"Caller Name\" <sip:caller@example.com>;tag=1928301774\r\n"
               "Call-ID: a84b4c76e66710@pc33.example.com\r\n"
               "CSeq: 314159 INVITE\r\n"
               "Contact: <sip:caller@pc33.example.com>\r\n"
               "Content-Type: application/sdp\r\n"
               "Content-Length: 204\r\n"
               "\r\n"
               "v=0\r\n"
               "o=caller 53655765 2353687637 IN IP4 pc33.example.com\r\n"
               "s=Session\r\n"
               "c=IN IP4 203.0.113.1\r\n"
               "t=0 0\r\n"
               "m=audio 49170 RTP/AVP 0\r\n"
               "a=rtpmap:0 PCMU/8000\r\n"
               "m=video 51372 RTP/AVP 31\r\n"
               "a=rtpmap:31 H261/90000")
    server_address = ('127.0.0.1', 9999)

    # Create a Future to track connection loss
    on_con_lost = asyncio.get_event_loop().create_future()

    # Create UDP socket and protocol
    transport, protocol = await asyncio.get_event_loop().create_datagram_endpoint(
        lambda: MyDatagramProtocol(message, on_con_lost),
        remote_addr=server_address
    )

    try:
        # Wait for connection to be lost (e.g., after receiving response)
        await on_con_lost
    finally:
        transport.close()


asyncio.run(udp_client())
