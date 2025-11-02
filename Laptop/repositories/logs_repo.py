import json
from repositories.base_repo import BaseRepo


class LogsRepo(BaseRepo):

    def log_register(self, user_id: int):
        self._execute_query(
            "INSERT INTO logs (actor_user_id,action,payload_json) VALUES (?,?,?)",
            (user_id, "REGISTER", json.dumps({"user_id": user_id})),
        )
        self._commit()

    def log_login(self, user_id: int):
        self._execute_query(
            "INSERT INTO logs (actor_user_id,action,payload_json) VALUES (?,?,?)",
            (user_id, "LOGIN", json.dumps({"user_id": user_id})),
        )
        self._commit()

    def log_search(self, user_id: int):
        self._execute_query(
            "INSERT INTO logs (actor_user_id,action,payload_json) VALUES (?,?,?)",
            (user_id, "SEARCH_ROOMS", json.dumps({"user_id": user_id})),
        )
        self._commit()

    def log_book_room(self, user_id: int, booking_id: int):
        self._execute_query(
            "INSERT INTO logs (actor_user_id,action,payload_json) VALUES (?,?,?)",
            (user_id, "CREATE_BOOKING", json.dumps({"booking_id": booking_id})),
        )
        self._commit()

    def log_cancel_booking(self, user_id: int, booking_id: int):
        self._execute_query(
            "INSERT INTO logs (actor_user_id,action,payload_json) VALUES (?,?,?)",
            (user_id, "CANCEL_BOOKING", json.dumps({"booking_id": booking_id})),
        )
        self._commit()

    def log_use_room(self, user_id: int, room_id: int):
        self._execute_query(
            "INSERT INTO logs (actor_user_id,action,payload_json) VALUES (?,?,?)",
            (user_id, "USE_ROOM", json.dumps({"room_id": room_id})),
        )
        self._commit()

    def log_return_room(self, user_id: int, room_id: int):
        self._execute_query(
            "INSERT INTO logs (actor_user_id,action,payload_json) VALUES (?,?,?)",
            (user_id, "RETURN_ROOM", json.dumps({"room_id": room_id})),
        )
        self._commit()

    def get_all_logs(self, limit: int = 100) -> list:
        results = self._fetch_all(
            "SELECT l.log_id, l.actor_user_id, u.full_name, l.action, "
            "l.payload_json, l.created_at FROM logs l "
            "JOIN users u ON l.actor_user_id = u.user_id "
            "ORDER BY l.created_at DESC LIMIT ?",
            (limit,),
        )

        logs = []
        for row in results:
            logs.append(
                {
                    "log_id": row[0],
                    "user_id": row[1],
                    "user_name": row[2],
                    "action": row[3],
                    "payload": json.loads(row[4]) if row[4] else {},
                    "created_at": row[5],
                }
            )
        return logs

    def get_user_logs(self, user_id: int, limit: int = 50) -> list:
        results = self._fetch_all(
            "SELECT log_id, action, payload_json, created_at FROM logs "
            "WHERE actor_user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )

        logs = []
        for row in results:
            logs.append(
                {
                    "log_id": row[0],
                    "action": row[1],
                    "payload": json.loads(row[2]) if row[2] else {},
                    "created_at": row[3],
                }
            )
        return logs
