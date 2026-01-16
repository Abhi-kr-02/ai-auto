# WhatsApp Web Integration Guide

## 🎉 WhatsApp Web Automation is Now Implemented!

### ✅ What Was Added:

1. **Full Playwright Integration** in `channels.py`
2. **Session Persistence** - No need to scan QR code every time
3. **Human-like Typing** - Random delays between characters and words
4. **Auto-login** - Prompts for QR scan on first use, then remembers
5. **Smart Delays** - 60s ± 15s jitter (0.6s in development mode)

---

## 🚀 How to Use:

### Step 1: First Time Setup (QR Code Scan)

When you send your first message, a Chrome window will open:

```python
# The system will automatically:
1. Open WhatsApp Web in Chrome
2. Prompt: "📱 WhatsApp Web: Please scan QR code..."
3. Wait for you to scan with your phone
4. Save the session (never ask again!)
```

**Important:** Don't close the Chrome window manually. Let the system manage it.

### Step 2: Send a Test Message

```bash
# Using the API
POST http://127.0.0.1:8000/inbound-message

{
  "phone_number": "+919876543210",
  "contact_name": "Test User",
  "message_text": "Hi! Interested in Digital Marketing course",
  "channel": "whatsapp_web"
}
```

The system will:
1. Create a lead in database
2. Generate AI response (GPT-4)
3. Open WhatsApp Web
4. Send message with human-like typing
5. Log everything

---

## 🔧 Configuration:

### Environment Variables (.env)

```bash
# WhatsApp Web session storage location
WHATSAPP_SESSION_DIR=./whatsapp_session

# Development mode (faster delays for testing)
ENV=development
```

### Session Storage

- Session saved in `./whatsapp_session/` folder
- Contains login cookies and browser state
- Persists across restarts
- Delete folder to force re-login

---

## 🎯 How It Works:

### Complete Flow:

```
1. Website Form Submission
   ↓
2. POST /inbound-message (with channel: "whatsapp_web")
   ↓
3. Create Lead in Database
   ↓
4. Enqueue ai_engage job (priority 100)
   ↓
5. Celery Worker picks up job
   ↓
6. AI generates response using GPT-4
   ↓
7. channel_router.send() → WhatsAppWebAdapter
   ↓
8. Playwright opens Chrome (if not already open)
   ↓
9. Check if logged in (or scan QR code)
   ↓
10. Navigate to chat: wa.me/phone
   ↓
11. Type message with human-like delays:
    - Random delay per character (50-150ms)
    - Random pause between words (100-300ms)
    - Random delay before sending (0.5-1.5s)
   ↓
12. Press Enter to send
   ↓
13. Log success in database
```

---

## 🧪 Testing:

### Test 1: Direct Channel Test

```python
# In Python console
from channels import WhatsAppWebAdapter

# This will open WhatsApp Web
result = WhatsAppWebAdapter.send({
    "phone": "+919876543210",
    "body": "Test message from automation"
})

print(result)
# Output: {'status': 'sent', 'external_id': 'wa_web_1234567890', ...}
```

### Test 2: Full API Flow

```bash
# Use Swagger UI: http://127.0.0.1:8000/docs
# Or curl:

curl -X POST "http://127.0.0.1:8000/inbound-message" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "contact_name": "Rahul Kumar",
    "message_text": "I want to learn Digital Marketing",
    "channel": "whatsapp_web"
  }'
```

---

## 🎨 Human-Like Features:

### 1. Typing Speed
- Each character: 50-150ms delay
- Mimics real human typing

### 2. Word Pauses
- Between words: 100-300ms
- Natural conversation flow

### 3. Send Delay
- Before pressing Enter: 0.5-1.5s
- Like a human reviewing message

### 4. Message Delays
- **Production:** 60s ± 15s (45-75 seconds)
- **Development:** 0.6s (100x faster for testing)

---

## ⚙️ Advanced Configuration:

### Headless Mode (Production)

Edit `channels.py` line ~128:

```python
cls._browser_instance = cls._playwright.chromium.launch_persistent_context(
    user_data_dir=user_data_dir,
    headless=True,  # Change to True for production
    args=[...]
)
```

### Custom Delays

Edit `channels.py` line ~83:

```python
base_delay = 60  # Change to your preferred delay
jitter = random.uniform(-15, 15)  # Randomness range
```

---

## 🔍 Troubleshooting:

### Issue: "WhatsApp Web login required"
**Solution:** QR code wasn't scanned. Check Chrome window, scan QR with phone.

### Issue: Chrome window opens and closes immediately
**Solution:** Check if session folder has correct permissions. Delete `./whatsapp_session/` and try again.

### Issue: Message not sending
**Solutions:**
1. Check if phone number has WhatsApp account
2. Ensure phone number format: +[country code][number]
3. Check Chrome console for errors

### Issue: "Target closed" error
**Solution:** Don't close Chrome manually. Let the system manage it. If needed, restart:

```python
from channels import WhatsAppWebAdapter
WhatsAppWebAdapter.close()  # Reset session
```

---

## 🎯 For Your Course Selling Use Case:

### Setup AI Prompt

1. **Add to Database:**

```sql
INSERT INTO ai_models (id, company_id, model_name, system_prompt, temperature, max_tokens)
VALUES (
  'your-uuid',
  'company-uuid',
  'gpt-4o-mini',
  'You are a sales expert for [Your Course Platform]. 
   Your goal is to convince students to enroll in our courses.
   
   Available Courses:
   - Digital Marketing Course: ₹15,000 (3 months)
   - Web Development Course: ₹25,000 (6 months)
   - Data Science Course: ₹30,000 (6 months)
   
   Use persuasive language, understand customer needs, 
   and guide them towards enrollment. Be friendly and professional.',
  0.7,
  500
);
```

2. **Add Course Info to Knowledge Base:**

```sql
INSERT INTO ai_kb_docs (id, company_id, title, content, doc_type)
VALUES (
  'kb-uuid',
  'company-uuid',
  'Digital Marketing Course Details',
  'Course Duration: 3 months
   Price: ₹15,000
   Topics: SEO, Social Media, Google Ads, Email Marketing
   Job Opportunities: Digital Marketing Manager, SEO Specialist
   Average Salary: ₹4-8 LPA',
  'course_info'
);
```

---

## 📊 Monitoring:

### Check Logs

**Worker Terminal:** Shows message sending progress
```
✅ WhatsApp Web: Message sent to +919876543210
```

**Chrome DevTools:** Right-click → Inspect → Console tab

### Database Queries

```sql
-- Check sent messages
SELECT * FROM messages WHERE channel = 'wa_web' ORDER BY created_at DESC;

-- Check job status
SELECT * FROM jobs WHERE task_name = 'ai.engage' ORDER BY created_at DESC;

-- Check leads
SELECT * FROM leads ORDER BY created_at DESC;
```

---

## 🚀 Production Deployment:

### Checklist:

- [ ] Set `ENV=production` in .env
- [ ] Set `headless=True` in channels.py
- [ ] Increase `base_delay` to 60+ seconds
- [ ] Set up proper OPENAI_API_KEY
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL certificate
- [ ] Run on VPS/cloud server
- [ ] Keep Chrome window running (use screen/tmux)

---
