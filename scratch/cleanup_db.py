import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import create_app
from backend.models import Encaminhamento
from backend.extensions import db

app = create_app()

with app.app_context():
    # Let's delete the specific test-created referrals
    deleted_ids = [1, 3]
    for enc_id in deleted_ids:
        enc = Encaminhamento.query.get(enc_id)
        if enc:
            db.session.delete(enc)
            print(f"Deleted test encaminhamento ID={enc_id}")
    
    db.session.commit()
    print("Database cleanup completed successfully.")
