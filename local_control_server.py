from flask import Flask, request, jsonify
import pyautogui

app = Flask(__name__)

@app.route('/move_mouse', methods=['POST'])
def move_mouse():
    data = request.json
    direction = data.get('direction')
    distance = data.get('distance', 50)
    directions = {
        'up': (0, -distance),
        'down': (0, distance),
        'left': (-distance, 0),
        'right': (distance, 0)
    }
    if direction in directions:
        dx, dy = directions[direction]
        pyautogui.moveRel(dx, dy)
        return jsonify({"status": "success", "message": f"Moved mouse {direction}"})
    return jsonify({"status": "error", "message": "Invalid direction"}), 400

@app.route('/click', methods=['POST'])
def click():
    button = request.json.get('button', 'left')
    pyautogui.click(button=button)
    return jsonify({"status": "success", "message": f"Clicked {button} button"})

@app.route('/double_click', methods=['POST'])
def double_click():
    pyautogui.doubleClick()
    return jsonify({"status": "success", "message": "Double clicked"})

@app.route('/right_click', methods=['POST'])
def right_click():
    pyautogui.rightClick()
    return jsonify({"status": "success", "message": "Right clicked"})

@app.route('/type', methods=['POST'])
def type_text():
    text = request.json.get('text', '')
    if text:
        pyautogui.write(text)
        return jsonify({"status": "success", "message": f"Typed text: {text}"})
    return jsonify({"status": "error", "message": "No text provided"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
