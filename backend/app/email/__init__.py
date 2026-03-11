# Ensure all email models are registered in the SQLAlchemy mapper
# so that string-based relationship references resolve correctly.
from app.email.attachment_models import EmailAttachment  # noqa: F401
from app.email.synced_email_models import SyncedEmail  # noqa: F401
