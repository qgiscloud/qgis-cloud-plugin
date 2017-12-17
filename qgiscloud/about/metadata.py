import os
import platform

try:
    import ConfigParser
except ImportError:
    import configparser    

class MetaData():

    def __init__(self):
        try:
            self.config = configparser.ConfigParser()
            self.config.read(os.path.join(os.path.dirname(__file__),'..','metadata.txt'))
        except:
            self.config = ConfigParser.ConfigParser()
            self.config.read(os.path.join(os.path.dirname(__file__),'..','metadata.txt'))

    def name(self):
        return self.config.get('general', 'name')
        
    def description(self):
        return self.config.get('general', 'description')
        
    def version(self):
        return self.config.get('general', 'version')
