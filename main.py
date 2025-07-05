from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello from Render!"

@app.route("/process", methods=["POST"])
def process_video():
    data = request.get_json()
    # Your process logic here
    return jsonify({"message": "Processing started"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)