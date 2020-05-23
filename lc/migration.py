import re

registered = []

module_name_regex = re.compile('^.*m_([0-9]+)_([a-z_]+)')

class Migration:
    def __init__(self, version, name, method):
        self.version = int(version)
        self.name = name
        self.method = method

    def run(self, db):
        self.method(db)

def migration(method):
    version, name = module_name_regex.match(method.__module__).groups()
    registered.append(Migration(version, name, method))
