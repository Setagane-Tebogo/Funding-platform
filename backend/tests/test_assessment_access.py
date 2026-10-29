import os
import sys
import unittest

from fastapi import HTTPException
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
except ModuleNotFoundError as error:
    if error.name == "sqlalchemy":
        raise unittest.SkipTest("Install backend/requirements.txt to run the SQLAlchemy ownership integration tests.")
    raise

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
from main_fastapi import Base, BusinessAssessment, BusinessProfile, User, list_business_assessments


class AssessmentOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.owner = User(name="Owner", email="owner@example.test", password="unused", role="ENTREPRENEUR")
        self.other = User(name="Other", email="other@example.test", password="unused", role="ENTREPRENEUR")
        self.db.add_all([self.owner, self.other]); self.db.flush()
        self.profile = BusinessProfile(user_id=self.owner.id, business_name="Rural Grocery", industry="Retail", business_stage="Startup", description="Local shop", location="Rural Limpopo")
        self.db.add(self.profile); self.db.flush()
        self.db.add_all([BusinessAssessment(user_id=self.owner.id, profile_id=self.profile.id, business_key="a" * 64, score=67, assessment_json='{"band":"Promising"}'), BusinessAssessment(user_id=self.other.id, business_key="a" * 64, score=12, assessment_json='{"band":"Other"}')])
        self.db.commit()

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    def test_profile_history_is_owner_scoped(self):
        rows = list_business_assessments(self.profile.id, None, self.owner, self.db)
        self.assertEqual([row["score"] for row in rows], [67])

    def test_other_entrepreneur_cannot_read_profile_history(self):
        with self.assertRaises(HTTPException) as error:
            list_business_assessments(self.profile.id, None, self.other, self.db)
        self.assertEqual(error.exception.status_code, 404)

    def test_business_key_history_is_owner_scoped(self):
        rows = list_business_assessments(None, "a" * 64, self.owner, self.db)
        self.assertEqual([row["score"] for row in rows], [67])


if __name__ == "__main__":
    unittest.main()
