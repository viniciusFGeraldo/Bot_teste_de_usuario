from flask import Flask, jsonify
import json
import os

app = Flask(__name__)
servers_file = "servers.json"

def load_servers():
    if os.path.exists(servers_file):
        with open(servers_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

@app.route('/servidores', methods=['GET'])
def get_servidores():
    data = load_servers()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
