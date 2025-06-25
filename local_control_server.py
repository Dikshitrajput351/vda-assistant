from flask import Flask, request, jsonify
import pyautogui

app = Flask(__name__)

@app.route('/move_mouse', methods=['POST'])
def move_mouse():
    data = request.json
    direction = data.get('direction')
    distance = data.get('distance', 50)
    dx, dy = {'up': (0, -distance), 'down': (0, distance),
              'left': (-distance, 0), 'right': (distance, 0)}.get(direction, (0, 0))
    pyautogui.moveRel(dx, dy)
    return jsonify({'message': f'Moved {direction}'})


@app.route('/click', methods=['POST'])
def click():
    button = request.json.get('button', 'left')
    pyautogui.click(button=button)
    return jsonify({'message': 'Clicked'})


@app.route('/double_click', methods=['POST'])
def double_click():
    pyautogui.doubleClick()
    return jsonify({'message': 'Double Clicked'})


@app.route('/right_click', methods=['POST'])
def right_click():
    pyautogui.rightClick()
    return jsonify({'message': 'Right Clicked'})


@app.route('/type', methods=['POST'])
def type_text():
    text = request.json.get('text', '')
    pyautogui.typewrite(text)
    return jsonify({'message': f'Typed: {text}'})

if __name__ == '__main__':
    app.run(port=5001)
