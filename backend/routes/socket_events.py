from flask_socketio import SocketIO, disconnect
from backend.services import heartbeat_service


def register_socket_events(socketio: SocketIO):
    @socketio.on('connect')
    def handle_connect(*args):
        """
        :param args: 标识身份验证auth信息
        :return: 无意义
        """
        print('Client connected')
        heartbeat_service.start_heartbeat()  # 启动心跳自增
        socketio.start_background_task(_send_heartbeat_data)

    def _send_heartbeat_data():
        while True:
            # 发送 device_update（带自增值）
            socketio.emit('device_update', {'value': heartbeat_service.value})
            # 发送固定值 qaq
            socketio.emit('qaq', {'value': 0})
            socketio.sleep(1)  # 合并为每秒发送两个事件
