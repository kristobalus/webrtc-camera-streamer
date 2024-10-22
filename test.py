

import cv2

camera1 = cv2.VideoCapture(0)
camera1.set(cv2.CAP_PROP_FPS, 60)

while True:
    ret1, frame1 = camera1.read()
    # Resize the image
    frame1 = cv2.resize(frame1, (1024, 576))
    cv2.imshow('frame1', frame1)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera1.release()

cv2.destroyAllWindows()