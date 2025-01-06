from datetime import datetime
from web.database import init_flask_db, User
from web.routes.auth import unique_api_token
from werkzeug.security import generate_password_hash

db = init_flask_db()


def insert_admin_if_not_exists():
    user = db.session.query(User).filter_by(username='admin').first()
    if not user:
        user = User(
            name='Administrator',
            avatar=None,
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('123456'),
            role='admin',  # guest, user, admin
            verify_token=None,
            verified_at=datetime.now(),
            reset_expires=None,
            remember_token=None,
            api_token=unique_api_token(),
            rate_limit=0
        )
        db.session.add(user)
        db.session.commit()


if __name__ == '__main__':
    db.create_all()
    insert_admin_if_not_exists()
