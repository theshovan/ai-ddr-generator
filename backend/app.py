from flask import Flask
from flask_cors import CORS
from routes.generate import bp as generate_bp
from config import PORT

app = Flask(__name__)
CORS(app)

app.register_blueprint(generate_bp)

@app.route("/health")
def health():
    return {"status": "ok"}



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
