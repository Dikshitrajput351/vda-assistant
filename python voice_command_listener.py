import requests
import time
import speech_recognition as sr

def listen_for_commands():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🎤 Voice listener started. Say 'Hi VDA' to activate...")

    while True:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"🗣️ Heard: {command}")

            if "hi vda" in command:
                print("✅ Wake word detected. Listening for command...")
                with mic as source:
                    audio = recognizer.listen(source)
                try:
                    command = recognizer.recognize_google(audio).lower()
                    print(f"🎯 Command: {command}")
                    send_command_to_flask(command)
                except Exception as e:
                    print(f"❌ Command error: {e}")
        except:
            continue

def send_command_to_flask(command):
    try:
        response = requests.post("http://localhost:5000/api/command", json={"command": command})
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 Response: {data.get('response', 'No response')}")
        else:
            print(f"❌ Server error: {response.status_code}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    listen_for_commands()
