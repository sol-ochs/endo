from app.db.dynamodb import get_dynamodb_resource
from app.db.user_repository import UserRepository

def get_db():
    db_resource = get_dynamodb_resource()
    try:
        yield UserRepository(db_resource)
    finally:
        pass