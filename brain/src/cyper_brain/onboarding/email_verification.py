"""
Email Verification Service

Handles email verification for new user signups.
"""

import os
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Optional, Dict
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


@dataclass
class VerificationToken:
    """Email verification token"""
    user_id: str
    email: str
    token: str
    expires_at: float
    verified: bool = False
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return time.time() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if token is valid (not expired, not verified)"""
        return not self.verified and not self.is_expired()


class EmailVerificationService:
    """
    Email verification service
    
    Generates verification tokens and sends verification emails.
    """
    
    def __init__(self, sendgrid_api_key: Optional[str] = None):
        """
        Initialize email verification service
        
        Args:
            sendgrid_api_key: SendGrid API key (or from SENDGRID_API_KEY env)
        """
        self.api_key = sendgrid_api_key or os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@cypersecurity.com")
        self.base_url = os.getenv("APP_BASE_URL", "https://app.cypersecurity.com")
        
        if self.api_key:
            self.client = SendGridAPIClient(self.api_key)
        else:
            self.client = None
            logger.warning("SendGrid API key not configured")
        
        # In-memory token storage (use database in production)
        self.tokens: Dict[str, VerificationToken] = {}
    
    def generate_verification_token(
        self,
        user_id: str,
        email: str,
        expires_in: int = 86400  # 24 hours
    ) -> VerificationToken:
        """
        Generate email verification token
        
        Args:
            user_id: User ID
            email: Email address
            expires_in: Token expiry in seconds (default 24h)
        
        Returns:
            VerificationToken
        """
        token = secrets.token_urlsafe(32)
        expires_at = time.time() + expires_in
        
        verification = VerificationToken(
            user_id=user_id,
            email=email,
            token=token,
            expires_at=expires_at
        )
        
        self.tokens[token] = verification
        logger.info(f"Generated verification token for {email}")
        
        return verification
    
    def send_verification_email(self, verification: VerificationToken):
        """
        Send verification email
        
        Args:
            verification: Verification token object
        """
        if not self.client:
            logger.error("Cannot send verification email: SendGrid not configured")
            return
        
        verification_url = f"{self.base_url}/verify-email?token={verification.token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; }}
                .button {{ display: inline-block; padding: 14px 28px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
                .button:hover {{ background: #5568d3; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Verify Your Email</h1>
                </div>
                <div class="content">
                    <h2>Welcome to CyperSecurity Platform!</h2>
                    <p>Thank you for signing up. Please verify your email address to activate your account.</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                    <p><strong>This link expires in 24 hours.</strong></p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>CyperSecurity Platform | Automated Security Testing</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = Mail(
            from_email=self.from_email,
            to_emails=verification.email,
            subject="Verify your email address",
            html_content=html_content
        )
        
        try:
            response = self.client.send(message)
            if response.status_code == 202:
                logger.info(f"Verification email sent to {verification.email}")
            else:
                logger.error(f"Failed to send verification email: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
    
    def verify_token(self, token: str) -> Optional[VerificationToken]:
        """
        Verify token and mark email as verified
        
        Args:
            token: Verification token
        
        Returns:
            VerificationToken if valid, None otherwise
        """
        verification = self.tokens.get(token)
        
        if not verification:
            logger.warning(f"Invalid verification token: {token}")
            return None
        
        if verification.verified:
            logger.info(f"Token already verified: {token}")
            return verification
        
        if verification.is_expired():
            logger.warning(f"Expired verification token: {token}")
            return None
        
        # Mark as verified
        verification.verified = True
        logger.info(f"Email verified for {verification.email}")
        
        return verification
    
    def resend_verification(self, email: str) -> bool:
        """
        Resend verification email
        
        Args:
            email: Email address
        
        Returns:
            True if resent successfully
        """
        # Find existing token
        for verification in self.tokens.values():
            if verification.email == email and not verification.verified:
                # Generate new token
                new_verification = self.generate_verification_token(
                    user_id=verification.user_id,
                    email=email
                )
                self.send_verification_email(new_verification)
                return True
        
        logger.warning(f"No pending verification found for {email}")
        return False


class OnboardingService:
    """
    User onboarding service
    
    Manages multi-step onboarding flow.
    """
    
    def __init__(self):
        """Initialize onboarding service"""
        self.user_progress: Dict[str, Dict] = {}
    
    def start_onboarding(self, user_id: str, email: str) -> Dict:
        """
        Start onboarding flow
        
        Args:
            user_id: User ID
            email: Email address
        
        Returns:
            Initial onboarding state
        """
        onboarding = {
            "user_id": user_id,
            "email": email,
            "current_step": 1,
            "total_steps": 4,
            "completed_steps": [],
            "data": {},
            "started_at": time.time()
        }
        
        self.user_progress[user_id] = onboarding
        logger.info(f"Started onboarding for user {user_id}")
        
        return onboarding
    
    def get_current_step(self, user_id: str) -> Optional[Dict]:
        """Get current onboarding step"""
        progress = self.user_progress.get(user_id)
        if not progress:
            return None
        
        step_number = progress["current_step"]
        
        steps = {
            1: {
                "title": "Welcome",
                "description": "Let's get you set up",
                "fields": []
            },
            2: {
                "title": "Organization Setup",
                "description": "Tell us about your organization",
                "fields": ["organization_name", "industry", "company_size"]
            },
            3: {
                "title": "Team Invitation",
                "description": "Invite your team members",
                "fields": ["team_emails"],
                "optional": True
            },
            4: {
                "title": "Start Trial",
                "description": "Activate your 14-day free trial",
                "fields": ["accept_terms"]
            }
        }
        
        return steps.get(step_number)
    
    def complete_step(
        self,
        user_id: str,
        step_data: Dict
    ) -> Dict:
        """
        Complete current onboarding step
        
        Args:
            user_id: User ID
            step_data: Data for current step
        
        Returns:
            Updated onboarding state
        """
        progress = self.user_progress.get(user_id)
        if not progress:
            raise ValueError(f"No onboarding found for user {user_id}")
        
        current_step = progress["current_step"]
        progress["completed_steps"].append(current_step)
        progress["data"].update(step_data)
        
        # Move to next step
        if current_step < progress["total_steps"]:
            progress["current_step"] = current_step + 1
        else:
            progress["completed"] = True
            progress["completed_at"] = time.time()
            logger.info(f"Onboarding completed for user {user_id}")
        
        return progress
    
    def activate_trial(self, user_id: str) -> Dict:
        """
        Activate trial subscription
        
        Args:
            user_id: User ID
        
        Returns:
            Trial activation details
        """
        trial_length_days = 14
        trial_expires = time.time() + (trial_length_days * 24 * 60 * 60)
        
        trial_info = {
            "user_id": user_id,
            "trial_active": True,
            "trial_expires_at": trial_expires,
            "trial_length_days": trial_length_days,
            "plan": "pro",  # Trial is for Pro plan
            "scans_remaining": 1000  # Pro plan limit
        }
        
        logger.info(f"Activated {trial_length_days}-day trial for user {user_id}")
        
        return trial_info
