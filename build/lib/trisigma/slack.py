class Slack:
    """This class sends messages in a slack channel"""
    def __init__ (self, token, default_channel=None):
        """Constructor for Slack object.

        :param token: slack token
        :type token: string
        :param default_channel: Sets a default channel. If left blank, then the channel must be specified in every send() function instead.
        :type default_channel: string
        """
        self.token = token
        self.default_channel = default_channel

    def send (self, msg, channel=None):
        """Sends a message in a channel

        :param msg: content of the message
        :type msg: string
        :param channel: Optional only if there is already a default channel specified
        :type channel: string
        """
        if channel == None:
            channel = self.default_channel

        headers = {'Authorization': 'Bearer ' + self.token}
        uri = 'https://slack.com/api/chat.postMessage'
        data = {"channel": channel, "text": msg}
        resp = requests.post(uri, json=data, headers=headers).json()
        return(resp)


