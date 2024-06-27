

"""
Global setting of the trading platform.
"""

from logging import CRITICAL
from typing import Dict, Any
# from tzlocal import get_localzone_name

import yaml
import os
# import talib


abspath = os.path.dirname(os.path.abspath(__file__))
# settingfile to be used.
SETTING_FILE_NAME = abspath + '/settings.yaml'


class Aiconfig():

    # class static variable config is loaded as the unique config data
    config = {}
    
    def __init__(self) -> None:
        self.isconfig = False
    
    @staticmethod
    def _load_config() ->bool:
        """
        """
        success = False
        with open(SETTING_FILE_NAME) as readfile:
            Aiconfig.config = yaml.safe_load(readfile)
        if Aiconfig.config:
            success = True
        return success
    
    @staticmethod
    def get(name:str):
        """ get the value of the specific name in the configuration file
        """
        if name:
            if not Aiconfig.config:
                if not Aiconfig._load_config():
                    raise FileExistsError(f"can't get configuration file loaded. file name: {SETTING_FILE_NAME}")
                
            return Aiconfig.config[name]
        else:
            raise ValueError(f"Name invalid: {name}")

    @staticmethod
    def set(name:str, args):
        """
        set the value of the specific settings
        """
        if not Aiconfig.config:
            if not Aiconfig._load_config():
                raise FileExistsError(f"can't get configuration file loaded. file name: {SETTING_FILE_NAME}")
        
        if name and Aiconfig.config[name] and args:
            Aiconfig.config.update({name: args})

            with open(SETTING_FILE_NAME, 'w') as writefile:
                yaml.dump(Aiconfig.config, writefile)
        else:
            raise ValueError(f"Name invalid: {name} or vlue {args}")

    def add(name:str, **args):
        """
        add a name: values to the settings.
        """
        if not Aiconfig.config:
            if not Aiconfig._load_config():
                raise FileExistsError(f"can't get configuration file loaded. file name: {SETTING_FILE_NAME}")

        if name and args:
            if Aiconfig.config[name]:
                raise ValueError(f"Name already exist: {name}. you can use set() to change the value")
            
            Aiconfig.config[name]= args

            with open(SETTING_FILE_NAME, 'w') as writefile:
                yaml.dump(Aiconfig.config, writefile)
        else:
            raise ValueError(f"Name invalid: {name} or vlue {args}")
        
    def append_to_list(name:str, **args):
        if not Aiconfig.config:
            if not Aiconfig._load_config():
                raise FileExistsError(f"can't get configuration file loaded. file name: {SETTING_FILE_NAME}")
        print("Aiconfig.config[name] is ",Aiconfig.config[name])
        if name and Aiconfig.config[name] and args and isinstance(Aiconfig.config[name],list):
            list(Aiconfig.config[name]).append(args)

            with open(SETTING_FILE_NAME, 'w') as writefile:
                yaml.dump(Aiconfig.config, writefile)
        else:
            raise ValueError(f"Name invalid: {name} or vlue {args}")

    def save_config():
        """
        save the whole config back to the settings file
        any changes will be saved to the files
        """
        if not Aiconfig.config:
            Aiconfig.config = {}
        else:
            with open(SETTING_FILE_NAME, 'w') as writefile:
                yaml.dump(Aiconfig.config, writefile)


SETTINGS: Dict[str, Any] = {}


def load_settings() -> Dict[Any, Any]:
    # Load global setting from yaml file.
    Aiconfig._load_config()
    SETTINGS.update(Aiconfig.config)
    return SETTINGS


def save_settings(settings):
    Aiconfig.config.update(settings)
    Aiconfig.save_config()


load_settings()


def get_settings(prefix: str = "") -> Dict[str, Any]:
    prefix_length: int = len(prefix)
    settings = {k[prefix_length:]: v for k, v in SETTINGS.items() if k.startswith(prefix)}
    return settings


def initialize_settings_data():
    """
    """        
    data = {
            "font.family": "Arial",
            "font.size": 12,

            "log.active": True,
            "log.level": CRITICAL,
            "log.console": True,
            "log.file": True,

            "email.server": "smtp.eagloo.co.uk",
            "email.port": 465,
            "email.username": "",
            "email.password": "",
            "email.sender": "",
            "email.receiver": "",

            "datafeed.name": "",
            "datafeed.username": "",
            "datafeed.password": "",

            # "database.timezone": get_localzone_name(),
            "database.name": "sqlite",
            "database.database": "database.db",
            "database.host": "",
            "database.port": 0,
            "database.user": "",
            "database.password": "",

            "__version__": "1.0"
        }
    

    # Write YAML file
    with open(SETTING_FILE_NAME, 'w', encoding='utf8') as outfile:
        yaml.dump(data, outfile, default_flow_style=False, allow_unicode=True)

    # Read YAML file
    with open(SETTING_FILE_NAME, 'r') as stream:
        data_loaded = yaml.safe_load(stream)
        
    print(data_loaded)


def main():
    initialize_settings_data()
    pass


if __name__ == "__main__":
    main()