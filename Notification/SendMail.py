import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path


smtp_server = ""  #SMTP-Server
smtp_port = 587
username = ""
password = ""
NAME = "AI AGENT"

def sendmail(email, html_content):
    # SMTP-Server-Details


    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Startet TLS-Verschlüsselung
            server.login(username, password)


        # Ersetze Platzhalter im HTML-Template
        # E-Mail Nachricht erstellen
            msg = MIMEMultipart()
            msg['From'] = formataddr((NAME , username))
            msg['To'] = email
            msg['Subject'] = "NOTIFICATION"

        # E-Mail-Text und HTML hinzufügen
            msg.attach(MIMEText(html_content, "html", "utf-8"))



            server.sendmail(username, email, msg.as_string())
            print(f"E-Mail erfolgreich an {email} gesendet.")
            return 1
    except Exception as e:
        print(f"Fehler beim Senden an {email}: {e}")
        return 0

