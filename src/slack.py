class Slack:
    """This class sends messages in a slack channel"""
    def __init__ (self, token, default_channel=None):
        """Constructor
        :param token: slack token
        :param default_channel: (Optional) sets a default channel. If left blank, then the channel must be specified in every send() function instead.
        """
        self.token = token
        self.default_channel = default_channel

    def send (self, msg, channel=None):
        """Sends a message in a channel
        :param msg: content of the message
        :param channel: (Optional if there is already a default channel specified)
        """
        if channel == None:
            channel = self.default_channel

        headers = {'Authorization': 'Bearer ' + self.token}
        uri = 'https://slack.com/api/chat.postMessage'
        data = {"channel": channel, "text": msg}
        resp = requests.post(uri, json=data, headers=headers).json()
        return(resp)


