from flask import (Flask, render_template, request, jsonify)

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/guest')
def guest():
    return render_template('guest.html')


@app.route('/host')
def host():
    return render_template('host.html')


@app.route('/host-processor', methods=['POST'])
def get_data():
    if request.method == 'POST':
        print("Writing data to file...")
        with open("data.json", "wb") as fo:
            fo.write(request.get_data())
        return '', 200


@app.route('/guest-processor')
def set_data():
    with open('data.json', 'r') as dataFile:
        return dataFile.read()


@app.route('/video-test')
def video_test():
    print("Link:")
    return render_template("video-test.html")


if __name__ == '__main__':
    app.run()
