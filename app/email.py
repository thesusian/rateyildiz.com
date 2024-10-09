import resend
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

def send_verification_email(to_email: str, verification_code: str):
    to_email="mhmd7by7@gmail.com"
    try:
        resend.Emails.send({
            "from": "Rate Yildiz <noreply@rateyildiz.com>",
            "to": to_email,
            "subject": "Verify your student email for Rate Yildiz",
            "html": f"""
            <h1>Verify your student email for Rate Yildiz</h1>
            <p>Your verification code is: <strong>{verification_code}</strong></p>
            <p>This code will expire in 24 hours.</p>
            """
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
