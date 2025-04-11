# Notifier Application

This application will connect to configured Kafka instance, listen on configured Topic for messages to send.

Then, asynchronyously, will send those messages using configured SMTP server.

## Configuration

Application expects environment variables to be set:
- `KAFKA_ADDRESS` - **REQUIRED** comma separated list of Kafka bootstrap servers
- `KAFKA_USERNAME` **REQUIRED**
- `KAFKA_USERNAME` **REQUIRED**
- `KAFKA_SASL_MECHANISM` (defaults to `SCRAM-SHA-512`)
- `KAFKA_SECURITY_PROTOCOL` (defaults to `SASL_SSL`)
- `KAFKA_TOPIC_PREFIX` (defaults to ``)
- `GETI_NOTIFICATION_TOPIC` - **REQUIRED** Topic to listen to, make sure it's already created
- `SMTP_HOST` **REQUIRED**
- `SMTP_PORT` **REQUIRED**
- `SMTP_LOGIN`
- `SMTP_PASSWORD`
- `USE_START_TLS` - `true` or `false`, when set determines if `START_TLS` (default) or `TLS` would be used.
   If not set, `SMTP_PORT` will decide (`TLS` on port 465, `START_TLS` otherwise).

## Messages
Application expects messages to be in format:
```json
    {
        "subject": "Subject of the email",
        "to": "recipient_address@example.com",
        "from_address": "sender_address@example.com",
        "from_name": "Sender Name",
        "html_content": "HTML content of the email."
    }    
```
