# WhatsApp Integration Guide

Your AI support bot now supports WhatsApp messaging with a whitelist feature.

## Setup

### 1. WhatsApp Business API (Meta)

To use the official WhatsApp Business API:

1. Create a Meta Developer account: https://developers.facebook.com
2. Set up a WhatsApp Business account
3. Get your credentials:
   - Business Phone ID
   - Access Token
   - Verify Token (for webhook)

### 2. Environment Variables

Add these to your Render dashboard:

| Variable | Value | Description |
|----------|-------|-------------|
| `WHATSAPP_ENABLED` | `true` | Enable WhatsApp integration |
| `WHATSAPP_WHITELIST` | `+6583886330,+1234567890` | Comma-separated allowed phone numbers |
| `WHATSAPP_VERIFY_TOKEN` | `your-verify-token` | Webhook verification token |
| `WHATSAPP_ACCESS_TOKEN` | `your-access-token` | Meta API access token |
| `WHATSAPP_BUSINESS_PHONE_ID` | `123456789` | Your WhatsApp Business phone ID |

### 3. Webhook Configuration

In your Meta Developer Dashboard:
- Webhook URL: `https://your-app.onrender.com/whatsapp/webhook`
- Verify Token: Same as `WHATSAPP_VERIFY_TOKEN`
- Subscribe to: `messages` events

## How It Works

1. Customer sends WhatsApp message to your business number
2. Meta forwards it to your webhook (`/whatsapp/webhook`)
3. Bot checks if phone number is in whitelist
4. If whitelisted, bot processes the message and replies
5. If not whitelisted, customer gets "not authorized" message

## Testing

Send a test message via API:

```bash
curl -X POST https://your-app.onrender.com/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+6583886330",
    "message": "Hello from the bot!"
  }'
```

## Alternative: Third-Party Services

If Meta's API is too complex, you can use:
- **Twilio WhatsApp**: https://www.twilio.com/whatsapp
- **MessageBird**: https://messagebird.com/whatsapp
- **WATI**: https://wati.io

These services provide simpler APIs and often have free tiers.

## Security Notes

- Always use the whitelist to prevent abuse
- Keep your access tokens secret
- Use HTTPS for all webhook communications
- Rotate tokens regularly
