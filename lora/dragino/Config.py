import toml
import logging

DEFAULT_LOGGING_LEVEL=logging.DEBUG

class TomlConfig:
    """
    provided to read in a toml config file and store
    data into a dictionary

    WARNING: Validity of entries in config.toml is not checked

    """

    config=None

    def __init__(self,configFile,logging_level=DEFAULT_LOGGING_LEVEL):
        """
        Load the config data from file

        This is never written back to by this program
        """
        self.logger=logging.getLogger("Config")
        self.logger.setLevel(logging_level)

        try:
            self.config=toml.load(configFile)

        except Exception as e:
            self.logger.error(f"config load error {e}")

    def getConfig(self):
        """
        returns the config dictionary

        Use to simplify access to user settings

        e.g.

        A=TomlConfig()
        Retries=A.["LoraWan"]["Retries"]

        """
        return self.config


