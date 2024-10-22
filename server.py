import cv2
import asyncio
import aiohttp
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
import fractions
from datetime import datetime
from aiohttp_cors import ResourceOptions, setup
import numpy as np


class CustomVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_id):
        super().__init__()
        self.cap = cv2.VideoCapture(camera_id)
        self.frame_count = 0
        self.format = "rgb24"
        self.frame_rate = 100

        w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print('resolution is: ', w, 'x', h)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)

        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
        self.cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
        self.cap.set(cv2.CAP_PROP_SATURATION, 0.5)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)

    async def recv(self):
        self.frame_count += 1
        # print(f"Sending frame {self.frame_count}")
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame from camera")
            return None

        # Improve image quality by denoising
        # frame = cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
        # Sharpen the image
        # kernel = np.array([[0, -1, 0],
        #                    [-1, 5, -1],
        #                    [0, -1, 0]])
        # frame = cv2.filter2D(src=frame, ddepth=-1, kernel=kernel)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Add timestamp to the frame
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Current time with milliseconds
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        video_frame = VideoFrame.from_ndarray(frame, format=self.format)
        video_frame.pts = self.frame_count
        video_frame.time_base = fractions.Fraction(1, self.frame_rate)  # Use fractions for time_base

        return video_frame


async def index(request):
    content = open("client.html", "r").read()
    return web.Response(content_type="text/html", text=content)


async def offer(request):
    params = await request.json()
    print(params)

    camera_id = params["camera_id"]
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

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

    return web.json_response(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    )


pcs = set()


async def cleanup_pcs():
    while True:
        await asyncio.sleep(10)
        for pc in set(pcs):
            if pc.iceConnectionState == "closed":
                pcs.discard(pc)


app = web.Application()
app.add_routes([
    web.get("/", index),
    web.post("/offer", offer)
])

# Set up CORS
cors = setup(app, defaults={
    "*": ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

# Add CORS to all routes
for route in list(app.router.routes()):
    cors.add(route)

web.run_app(app, port=9999)
