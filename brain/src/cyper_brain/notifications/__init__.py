# Notifications package initialization
from .email_service import EmailService, EmailTemplate, EmailDeliveryFailed

__all__ = ['EmailService', 'EmailTemplate', 'EmailDeliveryFailed']
