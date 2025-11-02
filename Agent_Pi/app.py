from flask import Flask, render_template, request, session, redirect, flash
from laptop_proxy import LaptopProxy

app = Flask(__name__)
app.secret_key = "0ee8bc37e262163f740eedee040698e8"


@app.route("/")
def home():
    if "token" not in session:
        return redirect("/login")
    payload = {"action": "VALIDATE_TOKEN", "token": session["token"]}
    resp = LaptopProxy.send(payload)
    if resp.get("status") != "ok":
        session.clear()
        return redirect("/login")
    flash(resp.get("message"), "error")
    return redirect("/dashboard")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    resp = None
    if request.method == "POST":
        payload = {
            "action": "REGISTER",
            "full_name": request.form["full_name"],
            "student_id": request.form["student_id"],
            "user_email": request.form["user_email"],
            "user_password": request.form["user_password"],
        }
        resp = LaptopProxy.send(payload)
        flash("Account creation was successful!", "success")
        return render_template("register.html")
    flash(resp.get("message"), "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    resp = None
    if request.method == "POST":
        payload = {
            "action": "LOGIN",
            "user_email": request.form["user_email"],
            "user_password": request.form["user_password"],
        }
        resp = LaptopProxy.send(payload)
        if resp.get("status") == "ok":
            session["token"] = resp["token"]
            session["user_id"] = resp["user_id"]
            session["first_name"] = resp["first_name"]
            return redirect("/dashboard")
        flash(resp.get("message"), "error")
        return render_template("login.html", resp=resp)

    if "token" not in session:
        return render_template("login.html")
    payload = {"action": "VALIDATE_TOKEN", "token": session["token"]}
    resp = LaptopProxy.send(payload)
    if resp.get("status") != "ok":
        session.clear()
        return render_template("login.html")
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    if "token" not in session:
        return redirect("/login")
    payload = {"action": "VALIDATE_TOKEN", "token": session["token"]}
    resp = LaptopProxy.send(payload)
    if resp.get("status") != "ok":
        session.clear()
        return redirect("/login")
    else:
        return render_template("dashboard.html", first_name=session.get("first_name"))


@app.route("/dashboard", methods=["POST"])
def search():
    if "token" not in session:
        return render_template("error.html")
    selected_date = request.form["date_picker"]
    return redirect(f"/dashboard/{selected_date}")


@app.route("/dashboard/<selected_date>")
def dashboard_with_search(selected_date):
    if "token" not in session:
        return render_template("error.html")
    payload = {
        "action": "SEARCH_ROOMS",
        "date": selected_date,
        "token": session["token"],
    }
    resp = LaptopProxy.send(payload)
    if resp.get("reason") == "invalid_token":
        session.clear()
        return render_template("error.html")
    elif resp.get("status") == "ok":
        return render_template(
            "dashboard.html",
            resp=resp,
            selected_date=selected_date,
            first_name=session.get("first_name"),
        )
    else:
        flash(resp.get("message"), "error")
        return redirect("/dashboard")


@app.route("/finalise-booking", methods=["POST"])
def finalise_booking():
    if "token" not in session:
        return render_template("error.html")
    selected_date = request.form["selected_date"]
    selected_slot = request.form["selected_slot"]
    room_id = request.form["room_id"]
    room_name = request.form["room_name"]
    if not (selected_date and room_id and selected_slot and room_name):
        return redirect("/dashboard")
    payload = {
        "action": "FINALISE_BOOKING",
        "selected_date": selected_date,
        "selected_slot": selected_slot,
        "room_id": room_id,
        "token": session["token"],
    }
    resp = LaptopProxy.send(payload)
    if resp.get("status") == "ok":
        return render_template(
            "finalise-booking.html",
            resp=resp,
            selected_date=selected_date,
            selected_slot=selected_slot,
            room_id=room_id,
            room_name=room_name,
        )
    elif resp.get("reason") == "invalid_token":
        session.clear()
        return render_template("error.html")
    else:
        flash(resp.get("message"), "error")
        return redirect(f"/dashboard/{selected_date}")


@app.route("/book-room", methods=["POST"])
def book_room():
    if "token" not in session:
        return render_template("error.html")
    selected_date = request.form["selected_date"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    room_id = request.form["room_id"]
    room_name = request.form["room_name"]

    payload = {
        "action": "CREATE_BOOKING",
        "selected_date": selected_date,
        "start_time": start_time,
        "end_time": end_time,
        "room_id": room_id,
        "token": session["token"],
    }
    resp = LaptopProxy.send(payload)
    if resp.get("status") == "ok":
        return render_template(
            "book-room.html",
            selected_date=selected_date,
            start_time=start_time,
            end_time=end_time,
            room_name=room_name,
            first_name=session.get("first_name"),
        )
    elif resp.get("reason") == "invalid_token":
        session.clear()
        return render_template("error.html")
    else:
        flash(resp.get("message"), "error")
        return redirect(f"/dashboard/{selected_date}")


@app.route("/my-bookings", methods=["GET", "POST"])
def my_bookings_page():
    if "token" not in session:
        return render_template("error.html")
    payload = {"action": "VIEW_BOOKINGS", "token": session["token"]}
    resp = LaptopProxy.send(payload)
    if resp.get("status") == "ok":
        return render_template("my-bookings.html", resp=resp)
    elif resp.get("reason") == "invalid_token":
        session.clear()
        return render_template("error.html")
    else:
        flash(resp.get("message"), "error")
        return redirect("/dashboard")


@app.route("/cancel-booking", methods=["POST"])
def cancel_booking():
    if "token" not in session:
        return render_template("error.html")
    booking_id = request.form["booking_id"]
    selected_date = request.form["date"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    room_name = request.form["room_name"]
    payload = {
        "action": "CANCEL_BOOKING",
        "booking_id": booking_id,
        "token": session["token"],
    }
    resp = LaptopProxy.send(payload)
    if resp.get("status") == "ok":
        return render_template(
            "cancel-booking.html",
            selected_date=selected_date,
            start_time=start_time,
            end_time=end_time,
            room_name=room_name,
            first_name=session.get("first_name"),
        )
    elif resp.get("reason") == "invalid_token":
        session.clear()
        return render_template("error.html")
    else:
        flash(resp.get("message"), "error")
        return redirect(f"/my-bookings")


@app.route("/check-in", methods=["POST"])
def use_room():
    if "token" not in session:
        return render_template("error.html")
    booking_id = request.form["booking_id"]
    selected_date = request.form["date"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    room_name = request.form["room_name"]
    room_id = request.form["room_id"]

    payload = {
        "action": "USE_ROOM",
        "booking_id": booking_id,
        "room_id": room_id,
        "token": session["token"],
    }
    resp = LaptopProxy.send(payload)
    if resp.get("status") == "ok":
        return render_template(
            "use-room.html",
            selected_date=selected_date,
            start_time=start_time,
            end_time=end_time,
            room_name=room_name,
            room_id=room_id,
            booking_id=booking_id,
        )
    elif resp.get("reason") == "invalid_token":
        session.clear()
        return render_template("error.html")
    else:
        flash(resp.get("message"), "error")
        return redirect(f"/my-bookings")


@app.route("/check-out", methods=["POST"])
def return_room():
    if "token" not in session:
        return render_template("error.html")
    room_name = request.form["room_name"]
    room_id = request.form["room_id"]
    reason = request.form["reason"]
    payload = {
        "action": "RETURN_ROOM",
        "room_id": room_id,
        "reason": reason,
        "token": session["token"],
    }
    resp = LaptopProxy.send(payload)
    if resp.get("status") == "ok":
        if reason == "timed_out":
            flash(
                f"You have been checked out of room {room_name} because your booking has ended",
                "info",
            )
        return redirect("/my-bookings")
    elif resp.get("reason") == "invalid_token":
        session.clear()
        return render_template("error.html")
    else:
        flash(resp.get("message"), "error")
        return redirect("/my-bookings")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# FOR TESTING #
# @app.route("/dashboard")
# def dashboard():
#     return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
