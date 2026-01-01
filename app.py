from flask import Flask, request, jsonify, render_template
from get_response import get_response
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"reply": "Please type a message."})
    reply = get_response(message)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000)