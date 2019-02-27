from os import path
from json import loads
from configparser import ConfigParser


class OnaConfigParser:
    def __init__(self, filename):
        self.parser = ConfigParser()
        dir = path.dirname(path.realpath(__file__))
        self.parser.read(path.join(dir, "config", filename))

    def __getattr__(self, key):
        try:
            # search all sections for the key, return None if not found
            value = next(self.parser[section][key] for section in self.parser if key in self.parser[section])
        except StopIteration:
            return None

        # the value will be converted to a python object
        return loads(value)
