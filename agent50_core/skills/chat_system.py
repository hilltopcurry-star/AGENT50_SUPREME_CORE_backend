class ChatSkill:
    def get_socket_setup(self):
        return """
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    emit('response', {'data': 'Message received!'}, broadcast=True)
"""