import smtplib
import os

EMAIL = os.environ.get('EMAIL')
PWD = os.environ.get('PWD')
TO_EMAIL = os.environ.get('FROM_EMAIL')

class Contact:

    def __init__(self, name, email, body):
        self.name = name
        self.email = email
        self.body = body


    def send_message(self):
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=EMAIL, password=PWD)
            connection.sendmail(
                from_addr=EMAIL,
                to_addrs=TO_EMAIL,
                msg=f"{self.name}\n{self.email}\n{self.body}"
            )
