import speech_recognition as sr

def capture_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
    return recognizer.recognize_google(audio)
