# stabilizerbot
Stabilizerbot is a bot for mediawiki FlaggedRevs extension that stabilizes articles automatically when specific rules are met. If you're planning to use this in Wikimedia foundation project, then you don't need to run the bot. It can be done for you.

### Dependencies
You're expected to have python 3 installed, rest of dependencies should be included in the source. Currently stabilizerbot is tested in python 3.6 and 3.4.

### Rules
List of currently supported rules:
* Anonreverts
* Abusefilters
* Greylist
* ORES

### Installing
Recommended way to download stabilizerbot is to do it using Git, so you can keep it updated easily.
Download over https:
```
git clone https://github.com/4shadoww/stabilizerbot.git
```
Download over ssh:
```
git clone git@github.com:4shadoww/stabilizerbot.git
```

Running stabilizerbot is pretty straightforward:
```
./stabilizer.py
```
But before running you should configure your bot correctly and create user-config.py for pywikibot.

### Configuration
First you should create user-config.py for pywikibot:
```python
# -*- coding: utf-8  -*-
from __future__ import unicode_literals
family = 'wikipedia'
mylang = 'en'
usernames['wikipedia']['en'] = u'YourUsername'
```

Core config is located at "core/config.json". From there set "lang" variable to match your language and do localization to "core/dict.json".

Full explanion of config.json
```
{
	"lang": "fi", <- Your language
	"rules": ["anonreverts", "ores", "abusefilters", "greylist"], <- Rules that will be used
	"ign_rules": [], <- Rules that will be ignored
	"test": false, <- Test mode
	"required_score": 2, <- Score that is required in order to do stabilization
	"namespaces": [0], <- Namespaces
	"stream_url": "https://stream.wikimedia.org/v2/stream/recentchange", <- Recent changes stream url
	"config_mode": "online", <- Will config loaded from local files or from wiki page (online / offline)
	"online_conf_path": "Käyttäjä:VakauttajaBot/config.json", <- Wiki page path (online config)
	"enable_log": false, <- Enable log
	"status_log": true, <- Status log
	"status_lps": 10, <- Status logs per seconds
	"log_decision": "positive", <- Log decisions (positive / negative / both)
	"s_delay": 300 <- Seconds to wait before stabilization
}
```

### Testing
You can test bot safely without actually stabilizing articles by setting "test" option in "core/config.json" to "True".

### Support
If you are planning to use this on Wikimedia foundation project, then I can run the bot for you. Just contact me for example in meta or with email.

* Email: 4shadoww0@gmail.com
* Meta: https://meta.wikimedia.org/wiki/User:4shadoww
