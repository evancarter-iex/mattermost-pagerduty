# mattermost-pagerduty
Webhook middleware to accept pagerduty events and posting them into a channel.


#### Installing
Run `pip install -r requirements.txt`

#### Configuring
At a minimum you need to define your mattermost hook url with an environmental variable MATTERMOST_PAGERDUTY_URL.

#### Running
This application will by default listen on port `8000`. To start it run `python run.py` or alternatively run it in supervisord or similar.

#### Example request url
Using a json POST blob hit the following url to post to the channel "Town-square"

```
http://1.2.3.4/PagerDutyNotification?channel=town-square 
```
