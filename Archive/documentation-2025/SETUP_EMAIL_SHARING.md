# Email Sharing Setup Guide

The PDF export and email sharing functionality requires SMTP configuration. Here's how to set it up:

## Quick Setup

### 1. Using Gmail (Recommended for Testing)

Add these environment variables to your `.env` file:

```bash
# Gmail SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

**Important:** Use an App Password, not your regular Gmail password:

1. Go to Google Account settings
2. Enable 2-Factor Authentication
3. Generate an App Password for "Mail"
4. Use that 16-character password in `SMTP_PASSWORD`

### 2. Using Outlook/Hotmail

```bash
# Outlook SMTP Configuration
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
FROM_EMAIL=your-email@outlook.com
```

### 3. Using Custom SMTP Server

```bash
# Custom SMTP Configuration
SMTP_HOST=your-smtp-server.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password
FROM_EMAIL=noreply@yourcompany.com
```

## Testing Configuration

1. **Check Configuration Status:**

   ```bash
   curl http://localhost:8765/api/v1/config/status
   ```

2. **Test Email Configuration:**

   ```bash
   curl http://localhost:8765/api/v1/config/email/test
   ```

3. **Restart Backend:**
   After updating `.env`, restart the backend server:

   ```bash
   # Kill existing process
   pkill -f "uvicorn app.main:socket_app"

   # Start again
   cd backend
   python -m uvicorn app.main:socket_app --host 0.0.0.0 --port 8765 --reload
   ```

## Features Enabled by Email Configuration

✅ **PDF Export** - Works without email configuration  
✅ **Email Sharing** - Requires SMTP configuration  
✅ **Alert Notifications** - Requires SMTP configuration  
✅ **Scheduled Reports** - Requires SMTP configuration

## Troubleshooting

### Common Issues

1. **"Email service not configured"**

   - Check that all SMTP environment variables are set
   - Restart the backend server after updating `.env`

2. **"Authentication failed"**

   - For Gmail: Use App Password, not regular password
   - For Outlook: Enable "Less secure app access" or use App Password
   - Check username/password are correct

3. **"Connection refused"**

   - Check SMTP_HOST and SMTP_PORT are correct
   - Ensure firewall allows outbound connections on SMTP port

4. **"SSL/TLS errors"**
   - Most modern SMTP servers use port 587 with STARTTLS
   - Port 465 uses SSL, port 25 is usually blocked

### Testing Email Manually

You can test email functionality using curl:

```bash
# Test sharing a research report
curl -X POST http://localhost:8765/api/v1/research/1/share \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["test@example.com"],
    "subject": "Test Report",
    "message": "This is a test email"
  }'
```

## Security Notes

- Never commit SMTP passwords to version control
- Use App Passwords instead of regular passwords when possible
- Consider using environment-specific `.env` files
- For production, use a dedicated email service (SendGrid, Mailgun, etc.)

## Production Recommendations

For production deployments, consider:

1. **Dedicated Email Service:** SendGrid, Mailgun, Amazon SES
2. **Environment Variables:** Use secure secret management
3. **Rate Limiting:** Configure email sending limits
4. **Monitoring:** Track email delivery success/failure rates

## Example Production Configuration

```bash
# Production SMTP (SendGrid example)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@yourcompany.com
```

---

**Need Help?** Check the configuration status at: http://localhost:8765/api/v1/config/status
