from passlib.hash import sha256_crypt
from repositories.base_repo import BaseRepo


class UsersRepo(BaseRepo):

    def email_exists(self, email: str) -> bool:
        user = self._fetch_one(
            "SELECT 1 FROM users WHERE LOWER(user_email)=?", (email.lower(),)
        )
        return user is not None

    def create_user(self, email, password, full_name, student_id, role="user") -> int:
        result = self._execute_query(
            "INSERT INTO users (user_email,user_password,full_name,student_id,role) VALUES (?,?,?,?,?)",
            (email, password, full_name, student_id, role),
        )
        self._commit()
        return result.lastrowid

    def verify_login(self, email, password) -> int:
        user_data = self._fetch_one(
            "SELECT user_password, user_id FROM users WHERE LOWER(user_email)=?",
            (email.lower(),),
        )
        if user_data:
            user_password, user_id = user_data
        if sha256_crypt.verify(password, user_password):
            return user_id
        else:
            return -1

    def get_user_by_id(self, user_id: int) -> dict:
        result = self._fetch_one(
            "SELECT user_id, user_email, full_name, student_id, role FROM users WHERE user_id=?",
            (user_id,),
        )
        if result:
            return {
                "user_id": result[0],
                "email": result[1],
                "full_name": result[2],
                "student_id": result[3],
                "role": result[4],
            }
        return None

    def get_first_name(self, user_id) -> str:
        user_data = self._fetch_one(
            "SELECT full_name FROM users WHERE user_id=?", (user_id,)
        )
        if user_data:
            full_name = str(user_data[0])
            first_name = full_name.split()[0]
            first_name = first_name.capitalize()
            return first_name
        else:
            return None

    def get_all_users(self) -> list:
        results = self._fetch_all(
            "SELECT user_id, user_email, full_name, student_id, role FROM users"
        )
        users = []
        for row in results:
            users.append(
                {
                    "user_id": row[0],
                    "email": row[1],
                    "full_name": row[2],
                    "student_id": row[3],
                    "role": row[4],
                }
            )
        return users

    def update_user(self, user_id: int, **kwargs) -> bool:
        fields = ["user_email", "full_name", "student_id"]
        updates = []
        params = []

        for field, value in kwargs.items():
            if field in fields:
                updates.append(f"{field}=?")
                params.append(value)

        if not updates:
            return False

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id=?"
        self._execute_query(query, params)
        self._commit()
        return True
