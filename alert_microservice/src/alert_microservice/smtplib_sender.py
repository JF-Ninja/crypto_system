from email.message import EmailMessage
import aiosmtplib
from alert_microservice.config import smtp_config


async def email_sender(email: str, ticker_name: str, price: float):
    message = EmailMessage()
    message["From"] = smtp_config.login
    message["To"] = email
    message["Subject"] = "Уведомление о пробитии цены."
    message.set_content(f"Тикер {ticker_name} пробил цену {price}")

    smtp_client = aiosmtplib.SMTP(hostname="smtp.gmail.com", port=587, start_tls=False, use_tls=False)
    async with smtp_client:
        await smtp_client.starttls()
        await smtp_client.login(smtp_config.login, smtp_config.password)
        await smtp_client.send_message(message)