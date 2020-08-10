from flask import (Flask, render_template, request, jsonify)

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/guest-youtube')
def guest_youtube():
    return render_template('guest-youtube.html')


@app.route('/host-youtube')
def host_youtube():
    return render_template('host-youtube.html')


@app.route('/guest-videojs')
def guest_videojs():
    return render_template('guest-videojs.html')


@app.route('/host-videojs')
def host_videojs():
    return render_template('host-videojs.html')


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
    return render_template("video-test.html")


@app.route('/videojs-freemode')
def videojs_freemode():
    return render_template("videojs-freemode.html")


if __name__ == '__main__':
    app.run()
