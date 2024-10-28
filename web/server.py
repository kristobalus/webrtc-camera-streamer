import cv2
import asyncio
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
import fractions
from aiohttp_cors import ResourceOptions, setup

pcs = set()


class CustomVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_id):
        super().__init__()
        self.frame_count = 0
        self.format = "rgb24"
        self.frame_rate = 30

        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FPS, self.frame_rate)

        w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print("resolution is: ", w, "x", h)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
        self.cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
        self.cap.set(cv2.CAP_PROP_SATURATION, 0.5)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        # self.cap.set(cv2.CAP_PROP_EXPOSURE, 1)

    async def recv(self):
        self.frame_count += 1
        # print(f"Sending frame {self.frame_count}")
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame from camera")
            return None

        # frame = cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)

        # def adjust_gamma(image, gamma=1.0):
        #     invGamma = 1.0 / gamma
        #     table = np.array([((i / 255.0) ** invGamma) * 255
        #                     for i in np.arange(0, 256)]).astype("uint8")
        #     return cv2.LUT(image, table)

        # # Apply gamma correction
        # frame = adjust_gamma(frame, gamma=1.2)  # Increase gamma for brightness

        # Create a sharpening kernel
        # sharpening_kernel = np.array([[0, -1, 0],
        #                             [-1, 5, -1],
        #                             [0, -1, 0]])

        # # Apply the sharpening filter
        # frame = cv2.filter2D(frame, -1, sharpening_kernel)

        # # Create an edge enhancement kernel
        # edge_enhancement_kernel = np.array([[0, 0, 0],
        #                                     [-1, 1, 0],
        #                                     [0, 0, 0]])
        # # Apply the filter
        # frame = cv2.filter2D(frame, -1, edge_enhancement_kernel)

        # -- Histogram Equalization (Contrast Enhancement):
        # # Convert to YUV color space
        # yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)

        # # Apply histogram equalization on the Y channel (brightness)
        # yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])

        # # Convert back to BGR
        # frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        # -- end of histogram

        # Improve image quality by denoising
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # frame = cv2.resize(frame, (int(1270/4), int(720/4)), interpolation=cv2.INTER_LANCZOS4)

        # Add timestamp to the frame
        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Current time with milliseconds
        # cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        video_frame = VideoFrame.from_ndarray(frame, format=self.format)
        video_frame.pts = self.frame_count
        video_frame.pict_type = "NONE"
        video_frame.time_base = fractions.Fraction(
            1, self.frame_rate
        )  # Use fractions for time_base

        return video_frame


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
    video_track = CustomVideoStreamTrack(0)
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


async def on_web_index(request):
    content = open("web/index.html", "r").read()
    return web.Response(content_type="text/html", text=content)


async def on_web_offer(request):
    params = await request.json()
    print(params)
    sdp_answer = await create_sdp_answer(params["sdp"])
    return web.json_response(
        {"sdp": sdp_answer, "type": "answer"}
    )


def main():
    # Start the WebRTC server
    app = web.Application()
    app.add_routes([web.get("/", on_web_index), web.post("/offer", on_web_offer)])

    # Set up CORS
    cors = setup(
        app,
        defaults={
            "*": ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*"
            )
        },
    )
    for route in list(app.router.routes()):
        cors.add(route)

    web.run_app(app, port=9999)


main()
