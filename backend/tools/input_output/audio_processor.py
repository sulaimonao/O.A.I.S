import speech_recognition as sr

def capture_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
    output = recognizer.recognize_google(audio)
    log_audio_capture(user_id)  # Log the capture event
    return output

def log_audio_capture(user_id):
    task_type = 'audio_capture'
    input_code = 'Audio capture started'
    output = 'Audio captured successfully'
    status = 'success'

    log_task_execution(user_id, task_type, input_code, output, status)
