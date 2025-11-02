from datetime import datetime
from repositories.base_repo import BaseRepo


class BookingsRepo(BaseRepo):

    def create_booking(self, user_id, room_id, date, start_time, end_time) -> int:
        result = self._execute_query(
            "INSERT INTO bookings (user_id,room_id,date,start_time,end_time,status) VALUES (?,?,?,?,?,?)",
            (user_id, room_id, date, start_time, end_time, "valid"),
        )
        self._commit()
        return result.lastrowid

    def cancel_booking(self, booking_id) -> bool:
        self._execute_query(
            "UPDATE bookings SET status=? WHERE booking_id=?", ("cancelled", booking_id)
        )
        self._commit()
        status = self._fetch_one(
            "SELECT status FROM bookings WHERE booking_id=?", (booking_id,)
        )
        if status[0] == "cancelled":
            return True
        else:
            return False

    def get_availabilities(self, room_id, date):
        booking_data = self._fetch_all(
            "SELECT start_time, end_time FROM bookings WHERE date=? AND room_id=? AND status IN (?, ?)",
            (date, room_id, "valid", "ongoing"),
        )
        slots = {f"{h:02d}:00:00": "available" for h in range(8, 18)}
        today_str = datetime.now().strftime("%Y-%m-%d")
        if date == today_str:
            current_hour = datetime.now().hour
            for h in range(8, min(current_hour + 1, 18)):
                slot_time = f"{h:02d}:00:00"
                if slot_time in slots:
                    slots[slot_time] = "occupied"

        for slot in slots.keys():
            for booking in booking_data:
                start, end = booking
                if start <= slot < end:
                    slots[slot] = "occupied"
                    break

        return slots

    def slot_available(self, room_id, date, time):
        bookings = self._fetch_one(
            "SELECT * FROM bookings WHERE date=? AND room_id=? AND status IN (?, ?) AND start_time=?",
            (date, room_id, "valid", "ongoing", time),
        )
        return bookings is None

    def full_slot_available(self, room_id, date, start_time, end_time):
        booking = self._fetch_one(
            "SELECT 1 FROM bookings WHERE date = ? AND room_id = ? AND status IN (?, ?) AND NOT (end_time <= ? OR start_time >= ?)",
            (date, room_id, "valid", "ongoing", start_time, end_time),
        )
        return booking is None

    def get_user_bookings(self, user_id):
        user_bookings = self._fetch_all(
            "SELECT booking_id, room_id, date, start_time, end_time, status FROM bookings WHERE user_id = ? AND status IN (?, ?, ?) ORDER BY date ASC, start_time ASC, end_time ASC",
            (user_id, "valid", "ongoing", "expired"),
        )
        bookings_dict = {}
        for booking in user_bookings:
            booking_id = booking[0]
            bookings_dict[booking_id] = {
                "room_id": booking[1],
                "date": booking[2],
                "start_time": booking[3],
                "end_time": booking[4],
                "status": booking[5],
            }
        return bookings_dict

    def get_booking_status(self, user_id, booking_id, room_id):
        booking = self._fetch_one(
            "SELECT status FROM bookings WHERE user_id = ? AND booking_id=? AND room_id=?",
            (user_id, booking_id, room_id),
        )
        if booking:
            return booking[0]
        else:
            return None

    def update_booking_statuses(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._execute_query(
            "UPDATE bookings SET status = 'expired' WHERE status = 'valid' AND datetime(date || ' ' || end_time) < datetime(?)",
            (now,),
        )
        self._execute_query(
            "UPDATE bookings SET status = 'ongoing' WHERE status = 'valid' AND datetime(date || ' ' || start_time) <= datetime(?) AND datetime(date || ' ' || end_time) >= datetime(?)",
            (now, now),
        )
        self._commit()

    def check_booking_status(self, booking_id):
        status = self._fetch_one(
            "SELECT status FROM bookings WHERE booking_id=?", (booking_id,)
        )
        return status[0]

    def get_all_bookings(self) -> list:
        bookings = self._fetch_all(
            "SELECT b.booking_id, b.user_id, u.full_name, b.room_id, r.name, "
            "b.date, b.start_time, b.end_time, b.status, b.created_at "
            "FROM bookings b "
            "JOIN users u ON b.user_id = u.user_id "
            "JOIN rooms r ON b.room_id = r.room_id "
            "ORDER BY b.created_at DESC"
        )
        result = []
        for row in bookings:
            result.append(
                {
                    "booking_id": row[0],
                    "user_id": row[1],
                    "user_name": row[2],
                    "room_id": row[3],
                    "room_name": row[4],
                    "date": row[5],
                    "start_time": row[6],
                    "end_time": row[7],
                    "status": row[8],
                    "created_at": row[9],
                }
            )
        return result
