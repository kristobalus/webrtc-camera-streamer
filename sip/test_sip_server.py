import asyncio
from sip_parser import parse_sip_message, build_200_ok_response


class UDPServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None
        pass

    def connection_made(self, transport):
        self.transport = transport
        print("Server is up and running")

    def datagram_received(self, data, addr):
        message = data.decode()
        print(f"Received message from {addr}:\n{message}")
        headers, sdp = parse_sip_message(message)

        if headers is not None and "invite" in headers["request-line"]:
            response = build_200_ok_response(message)
            self.transport.sendto(response.encode(), addr)
            return

    def error_received(self, exc):
        print(f"Error received: {exc}")

    def connection_lost(self, exc):
        print("Connection closed")


async def main():
    # Get a reference to the event loop
    loop = asyncio.get_running_loop()

    # Set up the UDP server
    print("Starting UDP server...")
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPServerProtocol(),
        local_addr=("127.0.0.1", 9999)
    )

    try:
        # Keep the server running indefinitely
        await asyncio.sleep(3600)  # Run for 1 hour (or adjust as needed)
    finally:
        # Close the transport (shutdown the server)
        transport.close()


# Run the asyncio server
asyncio.run(main())
