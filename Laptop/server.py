import socket, json, secrets
import threading
import time

from passlib.hash import sha256_crypt
from repositories.users_repo import UsersRepo
from repositories.bookings_repo import BookingsRepo
from repositories.rooms_repo import RoomsRepo
from repositories.logs_repo import LogsRepo


UsersRepo = UsersRepo() 
BookingsRepo = BookingsRepo() 
RoomsRepo = RoomsRepo() 
LogsRepo = LogsRepo()

HOST = "0.0.0.0"
PORT = 65000
SESSIONS = {}


def handle_register(req: dict) -> dict:
    email = req["user_email"].strip()
    full_name = req["full_name"].strip()
    student_id = req["student_id"].strip()
    password = sha256_crypt.encrypt(req["user_password"].strip())

    if UsersRepo.email_exists(email):
        return {
            "status": "error",
            "reason": "email_exists",
            "message": "An account with that email already exists.",
        }

    new_user_id = UsersRepo.create_user(email, password, full_name, student_id)
    LogsRepo.log_register(new_user_id)
    return {"status": "ok", "user_id": new_user_id}


def handle_login(req: dict) -> dict:
    email = req["user_email"].strip()
    password = req["user_password"].strip()

    if (UsersRepo.email_exists(email)) == False:
        return {
            "status": "error",
            "reason": "invalid_credentials",
            "message": "Your email or password is incorrect.",
        }

    user_id = UsersRepo.verify_login(email, password)
    if user_id == -1:
        return {
            "status": "error",
            "reason": "invalid_credentials",
            "message": "Your email or password is incorrect.",
        }
    else:
        token = secrets.token_hex(16)
        SESSIONS[token] = user_id
        LogsRepo.log_login(user_id)
        return {
            "status": "ok",
            "user_id": user_id,
            "first_name": UsersRepo.get_first_name(user_id),
            "token": token,
        }


def handle_search(req: dict) -> dict:
    token = req.get("token")
    if not token or token not in SESSIONS:
        return {"status": "error", "reason": "invalid_token"}

    date = req["date"]
    available_rooms = RoomsRepo.get_available_rooms()
    if not available_rooms:
        return {
            "status": "error",
            "reason": "no_available_rooms",
            "message": "There are no rooms available at the moment.",
        }
    else:
        rooms = []
        for room in available_rooms:
            availabilities = BookingsRepo.get_availabilities(room[1], date)
            rooms.append(
                {
                    "room_id": room[1],
                    "name": room[0],
                    "availabilities": [
                        {"slot": slot, "status": status}
                        for slot, status in availabilities.items()
                    ],
                }
            )
    user_id = SESSIONS[token]
    LogsRepo.log_search(user_id)
    return {"status": "ok", "rooms": rooms, "token": token}


def handle_finalise_booking(req: dict) -> dict:
    token = req.get("token")
    if not token or token not in SESSIONS:
        return {"status": "error", "reason": "invalid_token"}
    date = req["selected_date"]
    time = req["selected_slot"]
    room_id = req["room_id"]
    if (
        BookingsRepo.slot_available(room_id, date, time)
        and RoomsRepo.get_room_status(room_id) != "down"
    ):
        return {
            "status": "ok",
            "availabilities": BookingsRepo.get_availabilities(room_id, date),
            "token": token,
        }
    elif not BookingsRepo.slot_available(room_id, date, time):
        return {
            "status": "error",
            "reason": "slot_unavailable",
            "message": "That time slot is unavailable. Please select another.",
        }
    elif RoomsRepo.get_room_status(room_id) == "down":
        return {
            "status": "error",
            "reason": "room_down",
            "message": "That room is down at the moment. Please select another.",
        }
    else:
        return {
            "status": "error",
            "reason": "unknown",
            "message": "An error occured. Please try again.",
        }


def handle_book_room(req: dict) -> dict:
    token = req.get("token")
    if not token or token not in SESSIONS:
        return {"status": "error", "reason": "invalid_token"}
    date = req["selected_date"]
    start_time = req["start_time"]
    end_time = req["end_time"]
    room_id = req["room_id"]
    user_id = SESSIONS[token]
    if (
        BookingsRepo.full_slot_available(room_id, date, start_time, end_time)
        and RoomsRepo.get_room_status(room_id) != "down"
    ):
        booking_id = BookingsRepo.create_booking(
            user_id, room_id, date, start_time, end_time
        )
        LogsRepo.log_book_room(user_id, booking_id)

        return {"status": "ok", "token": token}
    elif not BookingsRepo.full_slot_available(room_id, date, start_time, end_time):
        return {
            "status": "error",
            "reason": "slot_unavailable",
            "message": "That time slot is unavailable. Please select another.",
        }
    elif RoomsRepo.get_room_status(room_id) == "down":
        return {
            "status": "error",
            "reason": "room_down",
            "message": "That room is down at the moment. Please select another.",
        }
    else:
        return {
            "status": "error",
            "reason": "unknown",
            "message": "An error occured. Please try again.",
        }


def handle_view_bookings(req: dict) -> dict:
    token = req.get("token")
    if not token or token not in SESSIONS:
        return {"status": "error", "reason": "invalid_token"}
    user_id = SESSIONS[token]

    if user_id:
        user_bookings = BookingsRepo.get_user_bookings(user_id)
        user_bookings = RoomsRepo.add_room_names_and_statuses(user_bookings)
        return {"status": "ok", "my_bookings": user_bookings, "token": token}
    elif not user_id:
        return {"status": "error", "reason": "invalid_token"}
    else:
        return {
            "status": "error",
            "reason": "unknown",
            "message": "An error occured. Please try again.",
        }


def handle_cancel_booking(req: dict) -> dict:
    token = req.get("token")
    booking_id = req["booking_id"]
    if not token or token not in SESSIONS:
        return {"status": "error", "reason": "invalid_token"}
    user_id = SESSIONS[token]
    if BookingsRepo.cancel_booking(booking_id):
        LogsRepo.log_cancel_booking(user_id, booking_id)
        return {"status": "ok", "token": token}
    else:
        return {
            "status": "error",
            "reason": "unknown",
            "message": "An error occured. Please try again.",
        }


def handle_use_room(req: dict) -> dict:
    token = req.get("token")
    booking_id = req["booking_id"]
    room_id = req["room_id"]
    if not token or token not in SESSIONS:
        return {"status": "error", "reason": "invalid_token"}
    user_id = SESSIONS[token]
    if (
        BookingsRepo.get_booking_status(user_id, booking_id, room_id) == "ongoing"
        and RoomsRepo.get_room_status(room_id) != "down"
    ):
        if RoomsRepo.update_room_status(room_id, "occupied"):
            LogsRepo.log_use_room(user_id, room_id)
            return {"status": "ok", "token": token}
        else:
            return {
                "status": "error",
                "reason": "couldnt_check_in",
                "message": "Unable to check in to room. Please try again.",
            }
    elif BookingsRepo.get_booking_status(user_id, booking_id, room_id) == "expired":
        return {
            "status": "error",
            "reason": "booking_expired",
            "message": "That booking has expired.",
        }
    elif BookingsRepo.get_booking_status(user_id, booking_id, room_id) == "cancelled":
        return {
            "status": "error",
            "reason": "booking_cancelled",
            "message": "That booking has been cancelled.",
        }
    elif BookingsRepo.get_booking_status(user_id, booking_id, room_id) == None:
        return {
            "status": "error",
            "reason": "booking_nonexistent",
            "message": "That booking does not exist.",
        }
    elif RoomsRepo.get_room_status == "down":
        return {
            "status": "error",
            "reason": "room_down",
            "message": "That room is currently down.",
        }
    else:
        return {
            "status": "error",
            "reason": "unknown",
            "message": "An error occured. Please try again.",
        }


def handle_return_room(req: dict) -> dict:
    token = req.get("token")
    room_id = req["room_id"]
    reason = req["reason"]
    print(room_id)
    if not token or token not in SESSIONS:
        return {"status": "error", "reason": "invalid_token"}

    user_id = SESSIONS[token]
    if RoomsRepo.get_room_status(room_id) != "down":
        if RoomsRepo.update_room_status(room_id, "available"):
            if reason == "timed_out":
                BookingsRepo.update_booking_statuses()
            LogsRepo.log_return_room(user_id, room_id)
            return {"status": "ok", "token": token}
        else:
            return {
                "status": "error",
                "reason": "couldnt_check_in",
                "message": "Unable to check out of room. Please try again.",
            }


def handle_validate_token(req: dict) -> dict:
    token = req.get("token")
    if token and token in SESSIONS:
        return {"status": "ok"}
    return {"status": "error", "reason": "invalid_token"}


def status_updater():
    while True:
        try:
            BookingsRepo.update_booking_statuses()
        except Exception as e:
            print(f"Error updating booking statuses: {e}")
        time.sleep(60)


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(4096)
                if not data:
                    continue
                try:
                    req = json.loads(data.decode())
                except:
                    resp = {"status": "error", "reason": "invalid_json"}
                else:
                    action = req.get("action")

                    if action == "REGISTER":
                        resp = handle_register(req)
                    elif action == "LOGIN":
                        resp = handle_login(req)
                    elif action == "SEARCH_ROOMS":
                        resp = handle_search(req)
                    elif action == "FINALISE_BOOKING":
                        resp = handle_finalise_booking(req)
                    elif action == "CREATE_BOOKING":
                        resp = handle_book_room(req)
                    elif action == "VIEW_BOOKINGS":
                        resp = handle_view_bookings(req)
                    elif action == "CANCEL_BOOKING":
                        resp = handle_cancel_booking(req)
                    elif action == "USE_ROOM":
                        resp = handle_use_room(req)
                    elif action == "RETURN_ROOM":
                        resp = handle_return_room(req)
                    elif action == "VALIDATE_TOKEN":
                        resp = handle_validate_token(req)
                    else:
                        resp = {"status": "error", "reason": "unknown_action"}
                conn.sendall(json.dumps(resp).encode())


if __name__ == "__main__":
    updater_thread = threading.Thread(target=status_updater, daemon=True)
    updater_thread.start()
    start_server()
