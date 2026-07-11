import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
_db = _client["studium"]

# Collections — one variable per collection, imported where needed
users = _db["users"]
syllabi = _db["syllabi"]
plans = _db["plans"]
quizzes = _db["quizzes"]
results = _db["results"]
