from os import path
from json import loads
from configparser import ConfigParser


class OnaConfigParser:
    def __init__(self, filename):
        self.parser = ConfigParser()
        self.parser.read(filename)

    def __getattr__(self, key):
        try:
            # Search all sections for the key, return None if not found
            value = next(self.parser[section][key] for section in self.parser if key in self.parser[section])
        except StopIteration:
            return None
        # The value will be converted to a python object
        return loads(value)

    def to_dict(self):
        return {k: loads(v) for section in self.parser.values() for k, v in section.items()}
