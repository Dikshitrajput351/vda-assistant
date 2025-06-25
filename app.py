import subprocess  # 🔧 Auto-start control server

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_dance.contrib.google import make_google_blueprint, google
import webbrowser
import re
import os
import pandas as pd
import traceback
import time
import requests

# 🔹 FAISS + SentenceTransformer
from sentence_transformers import SentenceTransformer
import faiss

# ⚠️ Optional GUI imports (only work locally)
try:
    import pyautogui
    import pygetwindow as gw
    import cv2
    import numpy as np
    from ultralytics import YOLO
    GUI_AVAILABLE = True
except Exception as e:
    print("[Warning] GUI features disabled:", e)
    GUI_AVAILABLE = False

# 🔀 Launch control server (local only)
if os.environ.get("RUN_LOCAL_SERVER") == "1":
    try:
        subprocess.Popen(["python", "local_control_server.py"])
        print("✅ Local control server launched.")
    except Exception as e:
        print("❌ Could not start control server:", e)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-very-secure-secret-key")

# 🔐 Google OAuth setup
google_bp = make_google_blueprint(
    client_id="YOUR_GOOGLE_CLIENT_ID",
    client_secret="YOUR_GOOGLE_CLIENT_SECRET",
    redirect_to="google_authorized"
)
app.register_blueprint(google_bp, url_prefix="/login")

# 📝 Load Q&A data and setup FAISS
embedder = SentenceTransformer('all-MiniLM-L6-v2')
faiss_index = None
qa_data = pd.DataFrame(columns=["question", "answer"])

if os.path.exists("data.csv"):
    try:
        qa_data = pd.read_csv("data.csv").dropna()
        questions = qa_data["question"].tolist()
        answers = qa_data["answer"].tolist()
        question_embeddings = embedder.encode(questions, convert_to_numpy=True)
        faiss_index = faiss.IndexFlatL2(question_embeddings.shape[1])
        faiss_index.add(question_embeddings)
        print("✅ FAISS index loaded with", len(questions), "entries.")
    except Exception as e:
        print("❌ Error loading FAISS index:", e)
else:
    print("❌ 'data.csv' not found. Starting with empty Q&A.")

# 🧐 Load YOLO model if possible
model = None
if GUI_AVAILABLE:
    model_path = "models/VDA_Detection - Copy/runs/detect/train/weights/best.pt"
    if os.path.exists(model_path):
        model = YOLO(model_path)

# 🌐 Local control server endpoint
LOCAL_CONTROL_SERVER = "http://127.0.0.1:5001"

# 🕘 Control functions (only if local)
def remote_move_mouse(direction, distance=100):
    try:
        resp = requests.post(f"{LOCAL_CONTROL_SERVER}/move_mouse", json={"direction": direction, "distance": distance}, timeout=5)
        return resp.json().get('message', 'No response')
    except Exception as e:
        return f"Error: {e}"

def remote_click(button='left'):
    try:
        resp = requests.post(f"{LOCAL_CONTROL_SERVER}/click", json={"button": button}, timeout=5)
        return resp.json().get('message', 'No response')
    except Exception as e:
        return f"Error: {e}"

def remote_double_click():
    try:
        resp = requests.post(f"{LOCAL_CONTROL_SERVER}/double_click", timeout=5)
        return resp.json().get('message', 'No response')
    except Exception as e:
        return f"Error: {e}"

def remote_right_click():
    try:
        resp = requests.post(f"{LOCAL_CONTROL_SERVER}/right_click", timeout=5)
        return resp.json().get('message', 'No response')
    except Exception as e:
        return f"Error: {e}"

def remote_type_text(text):
    try:
        resp = requests.post(f"{LOCAL_CONTROL_SERVER}/type", json={"text": text}, timeout=5)
        return resp.json().get('message', 'No response')
    except Exception as e:
        return f"Error: {e}"

def minimize_active_window():
    if not GUI_AVAILABLE:
        return False
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            active_window.minimize()
            time.sleep(0.5)
            return True
    except Exception as e:
        print("Error minimizing window:", e)
    return False

def get_answer_from_local_data(user_input):
    if faiss_index is None or qa_data.empty:
        return "Local data is empty or FAISS index not initialized."
    try:
        query_embedding = embedder.encode([user_input], convert_to_numpy=True)
        distances, indices = faiss_index.search(query_embedding, k=1)
        match_idx = indices[0][0]
        score = distances[0][0]
        return qa_data.iloc[match_idx]['answer'] if score < 1.5 else "माफ़ कीजिए, मुझे इसका जवाब नहीं मिला."
    except Exception as e:
        print("Error in FAISS search:", e)
        return "❌ Internal search error occurred."

def detect_objects():
    if not model:
        return []
    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    results = model(frame)
    detections = []
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()
        for box, cls in zip(boxes, classes):
            x1, y1, x2, y2 = box
            detections.append({"class": model.names[int(cls)], "center": [int((x1+x2)/2), int((y1+y2)/2)]})
    return detections

def process_command(command):
    cmd = command.lower().strip()
    if cmd.startswith("move") and any(d in cmd for d in ["up", "down", "left", "right"]):
        direction = re.search(r"(up|down|left|right)", cmd)
        return remote_move_mouse(direction.group()) if direction else "Invalid move command."
    if "right click" in cmd: return remote_right_click()
    if "double click" in cmd: return remote_double_click()
    if "click" in cmd: return remote_click()
    if cmd.startswith("type "): return remote_type_text(cmd[5:].strip())
    if cmd == "detect objects":
        if not GUI_AVAILABLE: return "YOLO object detection only available on desktop."
        detections = detect_objects()
        return f"Detected: {', '.join([d['class'] for d in detections])}" if detections else "No objects detected."
    if cmd.startswith("google search for "):
        q = cmd.replace("google search for", "", 1).strip()
        minimize_active_window()
        webbrowser.open(f"https://www.google.com/search?q={q.replace(' ', '+')}")
        return f"Searched Google for: {q}"
    if cmd.startswith("open youtube"):
        match = re.search(r"open youtube( and play (.+))?", cmd)
        minimize_active_window()
        q = match.group(2).strip() if match and match.group(2) else ""
        webbrowser.open(f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}" if q else "https://www.youtube.com")
        return f"Opened YouTube{' search: ' + q if q else ''}"
    if cmd.startswith("open "):
        site = cmd[5:].strip()
        minimize_active_window()
        webbrowser.open("https://" + site if not site.startswith("http") else site)
        return f"Opened {site}"
    if cmd.startswith("search for "):
        q = cmd.replace("search for", "", 1).strip()
        minimize_active_window()
        webbrowser.open(f"https://www.google.com/search?q={q.replace(' ', '+')}")
        return f"Searched for {q}"
    return get_answer_from_local_data(command)

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            session['user'] = email
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/login/google/authorized')
def google_authorized():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info.")
        return redirect(url_for('login'))
    session['user'] = resp.json().get("email", "Google User")
    return redirect(url_for('index'))

@app.route('/home')
def home(): return render_template('home.html')

@app.route('/search')
def search(): return render_template('search.html')

@app.route('/settings')
def settings(): return render_template('settings.html')

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.get_json()
    command = data.get('command', '')
    if not command:
        return jsonify({"error": "No command provided"}), 400
    try:
        response = process_command(command)
        return jsonify({"response": response})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)