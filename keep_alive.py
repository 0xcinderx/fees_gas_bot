
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is alive!"

@app.route('/status')
def status():
    return {"status": "running", "message": "Blockchain Fees Bot is working"}

def run():
    app.run(host='0.0.0.0', port=5000, debug=False)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
