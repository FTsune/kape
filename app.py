from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/_next/<path:path>')
def next_static(path):
    return send_from_directory('static/_next', path)

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static/_next/static', path)

if __name__ == '__main__':
    app.run(debug=True)
