import socket, json

HOST = "10.0.0.155"
PORT = 65000
ADDRESS = (HOST, PORT)


class LaptopProxy:
    @staticmethod
    def send(payload: dict) -> dict:
        """Send JSON payload to laptop socket server and return JSON reply."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(ADDRESS)
            s.sendall(json.dumps(payload).encode())
            chunks = []
            while True:
                part = s.recv(4096)
                if not part:
                    break
                chunks.append(part)

            data = b"".join(chunks)
            if not data:
                return {"status": "error", "reason": "no response"}

            try:
                return json.loads(data.decode())
            except Exception as e:
                print("Invalid JSON received:", data[:200])
                return {"status": "error", "reason": "invalid json", "details": str(e)}
