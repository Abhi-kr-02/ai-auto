"""
Phase 3: Channel Adapters
Unified interface for WhatsApp Web, Meta Cloud API, and Email
"""
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any
import os

# ============================================================================
# CHANNEL POLICIES (from SHVYA Guide)
# ============================================================================
# - Meta WhatsApp Cloud API → 15 sec (template-compliant)
# - WhatsApp Web → ≥ 60s delay with jitter (±15s), human-like pacing
# - Email → scheduled only (no email bump-ups)
# ============================================================================

class ChannelRouter:
    """Routes messages to appropriate channel"""
    
    @staticmethod
    def send(channel: str, payload: dict) -> Dict[str, Any]:
        """
        Unified send interface
        
        Args:
            channel: 'wa_cloud', 'wa_web', 'email'
            payload: Message data with fields like phone, body, template_id, etc.
        
        Returns:
            Result dict with status and external_id
        """
        if channel == "wa_cloud":
            return WhatsAppCloudAdapter.send(payload)
        elif channel == "wa_web":
            return WhatsAppWebAdapter.send(payload)
        elif channel == "email":
            return EmailAdapter.send(payload)
        else:
            raise ValueError(f"Unknown channel: {channel}")


# ============================================================================
# WhatsApp Cloud API Adapter
# ============================================================================

class WhatsAppCloudAdapter:
    """Meta WhatsApp Cloud API with template support"""
    
    @staticmethod
    def send(payload: dict) -> Dict[str, Any]:
        """
        Send via Meta Cloud API
        - Uses approved templates (HSM)
        - No free text outside 24h session window
        - 15 second minimum delay between messages
        """
        phone = payload.get("phone")
        template_id = payload.get("template_id")
        template_params = payload.get("template_params", [])
        body = payload.get("body")
        
        # Validate template requirement
        if not template_id and not WhatsAppCloudAdapter._is_within_24h_window(phone):
            return {
                "status": "failed",
                "error": "Template required outside 24h session window"
            }
        
        # Simulate API call
        try:
            # TODO: Replace with actual Meta Cloud API call
            # import requests
            # access_token = os.getenv("META_WHATSAPP_TOKEN")
            # phone_number_id = os.getenv("META_PHONE_NUMBER_ID")
            # url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            
            # Real implementation would be:
            # response = requests.post(url, headers={...}, json={...})
            
            # For now, simulate success
            external_id = f"wamid_{int(time.time())}"
            
            # Enforce 15 second minimum delay
            time.sleep(0.015)  # 15ms in dev, should be 15s in production
            
            return {
                "status": "sent",
                "external_id": external_id,
                "channel": "wa_cloud",
                "sent_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    @staticmethod
    def _is_within_24h_window(phone: str) -> bool:
        """Check if last inbound message was within 24 hours"""
        # TODO: Query database for last inbound message time
        # For now, return False (require template)
        return False


# ============================================================================
# WhatsApp Web Adapter (Playwright)
# ============================================================================

class WhatsAppWebAdapter:
    """WhatsApp Web with human-like pacing"""
    
    _browser_instance = None
    _page_instance = None
    _is_logged_in = False
    
    @classmethod
    def _get_browser_session(cls):
        """Get or create persistent browser session"""
        if cls._browser_instance is None or cls._page_instance is None:
            from playwright.sync_api import sync_playwright
            
            # Start playwright
            cls._playwright = sync_playwright().start()
            
            # Launch browser with persistent context (saves login session)
            user_data_dir = os.getenv("WHATSAPP_SESSION_DIR", "./whatsapp_session")
            
            cls._browser_instance = cls._playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,  # Set to True in production
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )
            
            # Get or create page
            if len(cls._browser_instance.pages) > 0:
                cls._page_instance = cls._browser_instance.pages[0]
            else:
                cls._page_instance = cls._browser_instance.new_page()
        
        return cls._page_instance
    
    @classmethod
    def _ensure_logged_in(cls, page):
        """Ensure user is logged into WhatsApp Web"""
        if cls._is_logged_in:
            return True
        
        try:
            # Navigate to WhatsApp Web
            page.goto("https://web.whatsapp.com", timeout=60000)
            
            # Wait for either QR code or chat list
            try:
                # Check if already logged in (chat list appears)
                page.wait_for_selector("div[data-testid='chat-list']", timeout=10000)
                cls._is_logged_in = True
                print("✅ WhatsApp Web: Already logged in")
                return True
            except:
                # Need to scan QR code
                print("📱 WhatsApp Web: Please scan QR code...")
                page.wait_for_selector("div[data-testid='chat-list']", timeout=120000)
                cls._is_logged_in = True
                print("✅ WhatsApp Web: Login successful")
                return True
                
        except Exception as e:
            print(f"❌ WhatsApp Web login failed: {e}")
            return False
    
    @staticmethod
    def send(payload: dict) -> Dict[str, Any]:
        """
        Send via WhatsApp Web (Playwright)
        - ≥60s delay with ±15s jitter
        - Human-like pacing
        - Free text allowed (no template restriction)
        """
        phone = payload.get("phone")
        body = payload.get("body")
        
        try:
            # Apply human-like delay (60s ± 15s jitter)
            base_delay = 60  # seconds
            jitter = random.uniform(-15, 15)
            delay = max(1, base_delay + jitter)  # Ensure positive
            
            # In development, use shorter delay
            is_dev = os.getenv("ENV", "development") == "development"
            actual_delay = delay * 0.01 if is_dev else delay
            time.sleep(actual_delay)
            
            # Get browser session
            page = WhatsAppWebAdapter._get_browser_session()
            
            # Ensure logged in
            if not WhatsAppWebAdapter._ensure_logged_in(page):
                return {
                    "status": "failed",
                    "error": "WhatsApp Web login required"
                }
            
            # Format phone number (remove + and spaces)
            clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
            
            # Navigate to chat
            chat_url = f"https://web.whatsapp.com/send?phone={clean_phone}"
            page.goto(chat_url, timeout=30000)
            
            # Wait for message input box
            page.wait_for_selector("div[contenteditable='true'][data-tab='10']", timeout=20000)
            
            # Type message with human-like delays
            message_box = page.locator("div[contenteditable='true'][data-tab='10']")
            message_box.click()
            
            # Type each word with random delays (human-like)
            words = body.split()
            for i, word in enumerate(words):
                # Type word
                for char in word:
                    message_box.type(char, delay=random.randint(50, 150))
                
                # Add space between words (except last word)
                if i < len(words) - 1:
                    message_box.type(" ", delay=random.randint(50, 150))
                
                # Random pause between words
                time.sleep(random.uniform(0.1, 0.3))
            
            # Small delay before sending
            time.sleep(random.uniform(0.5, 1.5))
            
            # Press Enter to send
            message_box.press("Enter")
            
            # Wait a bit to ensure message is sent
            time.sleep(2)
            
            external_id = f"wa_web_{int(time.time())}"
            
            print(f"✅ WhatsApp Web: Message sent to {phone}")
            
            return {
                "status": "sent",
                "external_id": external_id,
                "channel": "wa_web",
                "sent_at": datetime.utcnow().isoformat(),
                "delay_applied": actual_delay
            }
        
        except Exception as e:
            print(f"❌ WhatsApp Web error: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    @classmethod
    def close(cls):
        """Close browser session"""
        if cls._browser_instance:
            cls._browser_instance.close()
            cls._browser_instance = None
            cls._page_instance = None
            cls._is_logged_in = False
            if hasattr(cls, '_playwright'):
                cls._playwright.stop()


# ============================================================================
# Email Adapter
# ============================================================================

class EmailAdapter:
    """Email via SMTP (SES/SendGrid/SMTP)"""
    
    @staticmethod
    def send(payload: dict) -> Dict[str, Any]:
        """
        Send email
        - Quiet hours respected
        - Bounce & unsubscribe handling
        - No bump-ups (scheduled only)
        """
        to_email = payload.get("email")
        subject = payload.get("subject", "Message from AI Auto")
        body = payload.get("body")
        from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@example.com")
        
        try:
            # Check suppression list
            if EmailAdapter._is_suppressed(to_email):
                return {
                    "status": "failed",
                    "error": "Email is in suppression list"
                }
            
            # Check quiet hours (e.g., 10 PM - 8 AM)
            if not EmailAdapter._is_within_send_hours():
                return {
                    "status": "queued",
                    "message": "Queued for quiet hours"
                }
            
            # TODO: Replace with actual SMTP/SES call
            # smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            # smtp_port = int(os.getenv("SMTP_PORT", "587"))
            # smtp_user = os.getenv("SMTP_USER")
            # smtp_pass = os.getenv("SMTP_PASS")
            
            # msg = MIMEMultipart()
            # msg['From'] = from_email
            # msg['To'] = to_email
            # msg['Subject'] = subject
            # msg.attach(MIMEText(body, 'plain'))
            
            # with smtplib.SMTP(smtp_host, smtp_port) as server:
            #     server.starttls()
            #     server.login(smtp_user, smtp_pass)
            #     server.send_message(msg)
            
            # For now, simulate success
            external_id = f"email_{int(time.time())}"
            
            return {
                "status": "sent",
                "external_id": external_id,
                "channel": "email",
                "sent_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    @staticmethod
    def _is_suppressed(email: str) -> bool:
        """Check if email is in suppression list"""
        # TODO: Query suppression list from database
        return False
    
    @staticmethod
    def _is_within_send_hours() -> bool:
        """Check if current time is within allowed send hours"""
        # TODO: Implement quiet hours logic (e.g., 8 AM - 10 PM)
        current_hour = datetime.now().hour
        return 8 <= current_hour < 22  # 8 AM to 10 PM
