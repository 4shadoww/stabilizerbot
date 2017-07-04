from core.config_loader import cur_conf
import mwapi
import user_config

session = mwapi.Session(cur_conf["core"]["site"], user_agent="Yunomibot/0.1", api_path=cur_conf["core"]["api_path"])

def login():
    session.login(user_config.username, user_config.password)

    return True
