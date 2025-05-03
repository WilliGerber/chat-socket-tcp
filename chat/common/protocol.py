import json
import base64

def create_message(msg_type, sender, to, message="", file_content=None):
    return json.dumps({
        "type": msg_type,
        "from": sender,
        "to": to,
        "message": message,
        "file_content": file_content
    }).encode()

def parse_message(data):
    return json.loads(data.decode())