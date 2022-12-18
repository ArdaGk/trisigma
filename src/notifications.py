import ssl
import smtplib

#Abstract class Notifier
class Notifier:
    def __init__(self):
        pass

    def send(self, subject, body):
        pass

class GmailNotifier(Notifier):
    def __init__(self, username, password, recipients):
        self.username = username
        self.password = password
        self.recipients = recipients
        self.port = 465

    def send(self, subj, msg):
        port = 465  # For SSL
        password = "pgufemogpltrqsgk"
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(self.username, self.password)
            sender_email = self.username
            message = """\
            Subject: {subject}

            {body}""".format(subj, msg)

            for receiver in self.recipients:
                server.sendmail(sender_email, receiver, msg)

# SlackNotifier class
class SlackNotifier(Notifier):
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send(self, subj, msg):
        pass

class SlackNotifier(Notifier):
    def __init__ (self, token, channel):
        self.token = token
        self.channel = channel

    def send (self, subject, msg):
        headers = {'Authorization': 'Bearer ' + self.token}
        uri = 'https://slack.com/api/chat.postMessage'
        msg = f"{subject}, {msg}"
        data = {"channel": channel, "text": msg}
        resp = requests.post(uri, json=data, headers=headers).json()
        return(resp)


