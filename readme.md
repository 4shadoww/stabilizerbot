# stabilizerbot
Stabilizerbot is a bot for mediawiki FlaggedRevs extension that stabilizes articles automatically when specific rules are met. If you're planning to use this in Wikimedia foundation project, then you don't need to run the bot. It can be done for you.

### Dependencies
Requires Python 3. Python dependencies are the following: sseclient and mwapi. It's recommended to use the latest version of mwapi from Github and to not install it using pip since it haven't been updated in many years. 

### Rules
List of currently supported rules:
* Anonreverts
* Abusefilters
* Greylist
* Whitelist
* ORES

### Installing
Recommended way to download stabilizerbot is to do it using Git, so you can keep it updated easily.
Download over http:
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
But before running you should configure your bot correctly and create user_config.py for username and password.

### Configuration
First you should create user_config.py:
```python
username = "myUsername"
password = "myPassword"
```

Core config will be created when bot will be runned first time to "core/config.json". Note on first run bot only creates the configuration file. From there set "lang" variable to match your language and do localization to "core/dict.json".

### Testing
You can test bot safely without actually stabilizing articles by setting "test" option in "core/config.json" to "True".

### Support
If you are planning to use this on Wikimedia foundation project, then I can run the bot for you. Just contact me for example in meta or with email.

* Email: 4shadoww0@gmail.com
* Meta: https://meta.wikimedia.org/wiki/User:4shadoww
