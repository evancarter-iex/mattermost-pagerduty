from tornado.web import RequestHandler
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.gen import coroutine, Return
from tornado.ioloop import IOLoop
import os
import json


class PagerDutyHandler(RequestHandler):

    def initialize(self):
        """
        This is actually important. :D
        """
        self.mattermost_url = os.environ['MATTERMOST_PAGERDUTY_URL']

        """
        This maps message types to border
        colors for the message attachments
        """
        self.colors = {}
        self.colors['incident.trigger'] = '#FF0000'
        self.colors['incident.acknowledge'] = '#FFFF00'
        self.colors['incident.unacknowledge'] = '#FFFF00'
        self.colors['incident.resolve'] = 'good'
        self.colors['incident.assign'] = '#FFFF00'
        self.colors['incident.escalate'] = '#FF0000'
        self.colors['incident.delegate'] = '#FFFF00'

        self.FallbackText = ('##### Event \r\n' +
                             'Incident {} ([{}]({}))\r\n\r\n' +
                             '##### Subject\r\n{}' +
                             '\r\n\r\n' +
                             '##### Assigned to\r\n{}\r\n')

        """
        We need to map different incident details
        to different types of events.
        """
        self.incident_details = {}
        self.incident_details['incident.acknowledge'] = "Acknowledged by {}. "
        self.incident_details['incident.assign'] = "Assigned to {}. "
        self.incident_details['incident.delegate'] = ""
        self.incident_details['incident.escalate'] = "Incident escalated "
        self.incident_details['incident.resolve'] = "Resolved by {}. "
        self.incident_details['incident.trigger'] = ""
        self.incident_details['incident.unacknowledge'] = ""

    @coroutine
    def SendToMattermost(self, payload):
        """
        This takes care of the actual sending of payload to Mattermost.
        """
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch(
            self.mattermost_url,
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(payload))
        raise Return(response)

    @coroutine
    def post(self):
        data = json.loads(self.request.body)
        for message in data["messages"]:
            """
            We need the assignees multiple times, let's however
            only make the string once.
            """
            assignees = " & ".join(
                "[{}]({})".format(
                    assignee["assignee"]["summary"],
                    assignee["assignee"]["html_url"])
                for assignee in message["incident"]["assignments"]
            )

            incident_details = '[View incident details]({})'.format(
                message["incident"]["html_url"]
            )
            incident_details = (
                self.incident_details[message["event"]] + incident_details
            )

            if message["event"] == "incident.acknowledge":
                acked_by = " & " .join(
                    "[{}]({})".format(
                        acknowledger["acknowledger"]["summary"],
                        acknowledger["acknowledger"]["html_url"])
                    for acknowledger
                    in message["incident"]["acknowledgements"]
                )
                incident_details = incident_details.format(acked_by)

            elif message["event"] == "incident.assign":
                incident_details = incident_details.format(assignees)

            elif message["event"] == "incident.resolve":
                resolved_by = " & " .join(
                    "[{}]({})".format(
                        resolver["agent"]["summary"],
                        resolver["agent"]["html_url"])
                    for resolver
                    in message["log_entries"]
                )
                incident_details = incident_details.format(resolved_by)

            payload_dict = {
                'icon_url': 'https://i.imgur.com/LGpqJQy.png',
                'username': 'Pagerduty',
                'attachments': [
                    {
                        'fallback': self.FallbackText.format(
                            message["incident"]
                            ["status"],
                            message["incident"]
                            ["summary"],
                            message["incident"]
                            ["html_url"],
                            message["incident"]
                            ["title"],
                            assignees,
                        ),
                        'color': self.colors[message["event"]],
                        'fields':[
                            {
                                'short': True,
                                'title': 'Event',
                                'value': 'Incident {} ([{}]({})) (#{})'.format(
                                    message["incident"]
                                    ["status"],
                                    message["incident"]
                                    ["summary"],
                                    message["incident"]
                                    ["html_url"],
                                    message["incident"]
                                    ["incident_number"],
                                ),
                            },
                            {
                                'short': True,
                                'title': 'Subject',
                                'value': message["incident"]
                                ["title"],
                            },
                            {
                                'short': True,
                                'title': 'Assigned to',
                                'value': assignees,
                            },
                            {
                                'value': incident_details,
                            },
                        ]
                    }
                ]
            }

            """
            We will just fire and forget here. This is why the
            IOLoop.current().spawn_callback(
            self.SendToMattermost, payload_dict
            ) is used. If Pagerduty for instance is sending
            multiple messages at once this will incur multi
            second response times which might hurt Pagerduty
            performance. That is not something that we want to do.
            """

            IOLoop.current().spawn_callback(
                self.SendToMattermost, payload_dict
            )
        self.finish()
