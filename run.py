# run.py

from backend.app import create_app

app, socketio = create_app()

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    socketio.run(app, debug=True)
