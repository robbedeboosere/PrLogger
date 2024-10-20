from abc import ABC, abstractmethod
import firebase_admin
from firebase_admin import credentials, firestore
import sqlite3

# Abstract Database Strategy Interface
class PRDatabase(ABC):
    
    @abstractmethod
    def log_pr(self, user_id, exercise, weight):
        pass

    @abstractmethod
    def delete_pr(self, user_id, exercise):
        pass

    @abstractmethod
    def fetch_prs(self, user_id):
        pass

    @abstractmethod
    def fetch_leaderboard(self, exercise):
        pass

# Firebase Strategy Implementation
class FirebaseDB(PRDatabase):
    
    def __init__(self):
        cred = credentials.Certificate("path/to/your/firebase_credentials.json")
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def log_pr(self, user_id, exercise, weight):
        pr_data = {
            'exercise': exercise,
            'weight': weight,
            'date': firestore.SERVER_TIMESTAMP
        }
        self.db.collection('users').document(str(user_id)).collection('prs').add(pr_data)
        return f"Logged your PR: {exercise} - {weight}kg (Firebase)."
    
    def delete_pr(self, user_id, exercise):
        prs_ref = self.db.collection('users').document(str(user_id)).collection('prs')
        # Fetch the latest PR for the specified exercise
        latest_pr_query = prs_ref.where('exercise', '==', exercise).order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()

        latest_pr_doc = next(latest_pr_query, None)
        if latest_pr_doc:
            prs_ref.document(latest_pr_doc.id).delete()
            return f"Deleted the latest PR for {exercise}."
        else:
            return f"No PR found for {exercise}."

    def fetch_prs(self, user_id):
        prs_ref = self.db.collection('users').document(str(user_id)).collection('prs')
        docs = prs_ref.stream()

        pr_list = ""
        for doc in docs:
            pr = doc.to_dict()
            pr_list += f"{pr['exercise']}: {pr['weight']}kg\n"
        
        return pr_list if pr_list else "No PRs found (Firebase)."

    def fetch_leaderboard(self, exercise):
        return super().fetch_leaderboard(exercise)

# SQLite Strategy Implementation
class SQLiteDB(PRDatabase):
    
    def __init__(self):
        self.conn = sqlite3.connect('prlogger.db')
        self.c = self.conn.cursor()
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS prs (
                user_id INTEGER,
                exercise TEXT,
                weight INTEGER,
                date TEXT
            )
        ''')
        self.conn.commit()

    def log_pr(self, user_id, exercise, weight):
        self.c.execute('''
            INSERT INTO prs (user_id, exercise, weight, date)
            VALUES (?, ?, ?, datetime('now'))
        ''', (user_id, exercise, weight))
        self.conn.commit()
        return f"Logged your PR: {exercise} - {weight}kg."
    
    def delete_pr(self, user_id, exercise):
        # Find the latest PR for the specified exercise
        self.c.execute('SELECT weight FROM prs WHERE user_id=? AND exercise=? ORDER BY date DESC LIMIT 1', (user_id, exercise))
        latest_pr_id = self.c.fetchone()

        if latest_pr_id:
            self.c.execute('DELETE FROM prs WHERE weight=? AND user_id=? AND exercise=?', (latest_pr_id[0],user_id, exercise))
            self.conn.commit()
            return f"Deleted the latest PR for {exercise}."
        else:
            return f"No PR found for {exercise}."

    def fetch_prs(self, user_id):
        self.c.execute('SELECT exercise, weight, date FROM prs WHERE user_id=?', (user_id,))
        rows = self.c.fetchall()

        pr_list = ""
        for row in rows:
            pr_list += f"{row[0]}: {row[1]}kg on {row[2]}\n"

        return pr_list if pr_list else "No PRs found."
    
    def fetch_leaderboard(self, exercise):
            self.c.execute('SELECT user_id, weight FROM prs WHERE exercise=? ORDER BY weight DESC LIMIT 10', (exercise,))
            rows = self.c.fetchall()
            return rows  # Returns a list of tuples (user_id, weight)