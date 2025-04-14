import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import credentials

def send_new_site_user_email(email: str, shareLink: str, editLink: str):
    """Sends an email to the user when they add a site."""
    subj = 'Your diagram is ready!'
    body_html = \
        f"""<p>Hey!</p>
    <p>Your diagram is ready.
    You can share it with the link <a href="{shareLink}">{shareLink}</a></p>
    <p>If you like to delete the uploaded data, you can use the edit link <a href="{editLink}">{editLink}</a></p>"""

    body_plain = \
        f"""Hey!
        Your diagram is ready.
        You can share it with the link {shareLink}
        If you like to delete the uploaded data, you can use the edit link {editLink}"""
    send_email(email, subj, body_plain, body_html)


def send_email(email: str, subj: str, body_plain: str, body_html: str):
    SMTP_PORT = os.getenv("SMTP_PORT", credentials.SMTP_PORT)
    SMTP_SERVER = os.getenv("SMTP_SERVER", credentials.SMTP_SERVER)
    SENDER_E_MAIL = os.getenv("SENDER_E_MAIL", credentials.SENDER_E_MAIL)
    E_MAIL_PASSWORD = os.getenv("E_MAIL_PASSWORD", credentials.E_MAIL_PASSWORD)

    receiver_email = email
    message = MIMEMultipart("alternative")
    message["Subject"] = subj
    message["From"] = SENDER_E_MAIL
    message["To"] = receiver_email
    # write the text/plain part

    # convert both parts to MIMEText objects and add them to the MIMEMultipart message
    part1 = MIMEText(body_plain, "plain")
    part2 = MIMEText(body_html, "html")
    message.attach(part1)
    message.attach(part2)
    # send your email
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SENDER_E_MAIL, E_MAIL_PASSWORD)
        server.sendmail(
            SENDER_E_MAIL, receiver_email, message.as_string()
        )
    print('Sent')


