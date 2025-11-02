PRAGMA foreign_keys = ON;

CREATE TABLE users (
user_id INTEGER PRIMARY KEY AUTOINCREMENT,
user_email TEXT NOT NULL UNIQUE,
user_password TEXT NOT NULL,
full_name TEXT NOT NULL,
student_id TEXT UNIQUE,
role TEXT NOT NULL CHECK (role IN ('admin','user')),
created_at TEXT NOT NULL DEFAULT (datetime('now')),
CHECK ((role='admin' AND student_id IS NULL) OR (role='user' AND student_id IS NOT NULL))
);

CREATE TABLE rooms (
room_id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL UNIQUE,
status TEXT NOT NULL CHECK (status IN ('available','occupied','down')),
note TEXT,
created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE bookings (
booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER NOT NULL,
room_id INTEGER NOT NULL,
date TEXT NOT NULL,
start_time TEXT NOT NULL,
end_time TEXT NOT NULL,
status TEXT NOT NULL CHECK (status IN ('valid','cancelled','ongoing','expired')),
created_at TEXT NOT NULL DEFAULT (datetime('now')),
CHECK (end_time > start_time),
FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE logs (
log_id INTEGER PRIMARY KEY AUTOINCREMENT,
actor_user_id INTEGER NOT NULL,
action TEXT NOT NULL CHECK (action IN ('REGISTER','LOGIN','LOGOUT','SEARCH_ROOMS','CREATE_BOOKING','CANCEL_BOOKING','USE_ROOM','RETURN_ROOM')),
payload_json TEXT,
created_at TEXT NOT NULL DEFAULT (datetime('now')),
FOREIGN KEY (actor_user_id) REFERENCES users(user_id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX idx_bookings_user_time ON bookings(user_id,start_time);
CREATE INDEX idx_bookings_room_time ON bookings(room_id,start_time);
CREATE INDEX idx_logs_user_time ON logs(actor_user_id,created_at);

INSERT INTO users (user_email,user_password,full_name,student_id,role,created_at) VALUES
('admin@example.com','$5$rounds=535000$5cn.QebxhQ/uQ8fb$IuekiNo.ZbCRtlmEBN04uixu7MNVSboBEQsAR75ccF6','System Admin',NULL,'admin','2025-09-01 09:00:00'),
('alice@example.com','$5$rounds=535000$U0Z.wQmrUIq0Sajb$XKFEOGUGwUfAFrCROB.HqNrG4TlfXBi4PtsWtDiLquB','Alice Johnson','s4839201','user','2025-09-01 09:05:00'),
('bob@example.com','$5$rounds=535000$xSm/wlMxK6mmoWmg$pwcq90MkGU0n4nSa/GgyQO3HQY/bQYo2O/fZrNfuAi6','Bob Lee','s5192047','user','2025-09-01 09:10:00');

INSERT INTO rooms (name,status,note,created_at) VALUES
('R101','available',NULL,'2025-09-01 10:00:00'),
('R102','available',NULL,'2025-09-01 10:00:00'),
('R103','available',NULL,'2025-09-01 10:00:00'),
('R104','available',NULL,'2025-09-01 10:00:00'),
('R105','down','Projector fault','2025-09-01 10:00:00'),
('R201','available',NULL,'2025-09-01 10:00:00');

INSERT INTO bookings (user_id,room_id,date,start_time,end_time,status,created_at) VALUES
/*TESTING VALUE */(2,5,'2025-11-01','17:50:00','18:01:00','ongoing','2025-10-31 12:00:00'),
/*TESTING VALUE */(2,4,'2025-11-01','17:50:00','19:01:00','ongoing','2025-10-31 12:00:00'),
/*TESTING VALUE */(2,4,'2025-11-01','16:00:00','17:17:00','valid','2025-10-31 12:00:00'),
(2,3,'2025-09-05','09:00:00','10:00:00','expired','2025-09-01 12:00:00'),
(2,2,'2025-10-18', '14:00:00','16:00:00','cancelled','2025-10-10 08:30:00'),
(2,1,'2025-12-10', '10:00:00','12:00:00','valid','2025-10-25 09:00:00');


INSERT INTO logs (actor_user_id,action,payload_json,created_at) VALUES
(3,'REGISTER','{"user_id":3}','2025-09-01 09:10:30'),
(2,'REGISTER','{"user_id":2}','2025-09-01 09:05:30'),
(2,'LOGIN','{"user_id":2}','2025-09-01 11:45:00'),
(2,'SEARCH_ROOMS','{"user_id":2}','2025-09-01 11:50:00'),
(2,'CREATE_BOOKING','{"booking_id":1}','2025-09-01 12:00:10'),
(2,'USE_ROOM','{"room_id":1}','2025-09-05 09:02:00'),
(2,'RETURN_ROOM','{"room_id":1}','2025-09-05 09:55:00'),
(2,'SEARCH_ROOMS','{"user_id":2}','2025-10-10 08:20:00'),
(2,'CREATE_BOOKING','{"booking_id":2}','2025-10-10 08:30:10'),
(2,'CANCEL_BOOKING','{"booking_id":2}','2025-10-12 10:00:00'),
(2,'SEARCH_ROOMS','{"user_id":2}','2025-10-25 08:55:00'),
(2,'CREATE_BOOKING','{"booking_id":3}','2025-10-25 09:00:10');
