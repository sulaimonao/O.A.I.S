import cv2

def capture_video():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imshow('Video Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

def log_video_capture(user_id):
    task_type = 'video_capture'
    input_code = 'Video capture started'
    output = 'Video captured successfully'
    status = 'success'

    log_task_execution(user_id, task_type, input_code, output, status)
