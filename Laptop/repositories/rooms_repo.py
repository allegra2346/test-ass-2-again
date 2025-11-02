from repositories.base_repo import BaseRepo


class RoomsRepo(BaseRepo):

    def get_available_rooms(self) -> list:
        room_data = self._fetch_all(
            "SELECT name, room_id FROM rooms WHERE status  IN (?, ?)",
            ("available", "occupied"),
        )
        room_list = []
        for room in room_data:
            room_list.append(room)
        return room_list

    def add_room_names_and_statuses(self, bookings) -> dict:
        for booking_id, booking in bookings.items():
            room_details = self._fetch_one(
                "SELECT name, status FROM rooms WHERE room_id=?", (booking["room_id"],)
            )
            room_name = room_details[0]
            room_status = room_details[1]
            booking["room_name"] = room_name
            booking["room_status"] = room_status

        return bookings

    def get_room_status(self, room_id: int) -> str:
        result = self._fetch_one("SELECT status FROM rooms WHERE room_id=?", (room_id,))
        if result:
            return result[0]
        else:
            None

    def update_room_status(self, room_id, status, note=None) -> bool:
        if status not in ["available", "occupied", "down"]:
            return False

        if note:
            result = self._execute_query(
                "UPDATE rooms SET status=?, note=? WHERE room_id=?",
                (status, note, room_id),
            )
        else:
            result = self._execute_query(
                "UPDATE rooms SET status=? WHERE room_id=?", (status, room_id)
            )
        self._commit()
        if result.rowcount == 0:
            return False
        else:
            return True

    def get_all_rooms(self) -> list:
        results = self._fetch_all(
            "SELECT room_id, name, status, note FROM rooms ORDER BY name"
        )
        rooms = []
        for row in results:
            rooms.append(
                {"room_id": row[0], "name": row[1], "status": row[2], "note": row[3]}
            )
        return rooms
