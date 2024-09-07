# notifier/Notifier.py
from notifiers import get_notifier


class Notifier:
    def __init__(self, webhook_url):
        self.slack = get_notifier("slack")
        self.webhook_url = webhook_url

    def send_slack(self, subject, message):
        """Send a notification to Slack."""
        self.slack.notify(message=f"{subject} {message}", webhook_url=self.webhook_url)
