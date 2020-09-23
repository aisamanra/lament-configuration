import re

registered = []

module_name_regex = re.compile("^.*m_([0-9]+)_([a-z_]+)")


class Migration:
    def __init__(self, version, name, method):
        self.version = int(version)
        self.name = name
        self.method = method

    def run(self, db):
        self.method(db)


def migration(method):
    match = module_name_regex.match(method.__module__)
    if not match:
        raise Exception(f"Unable to find migration version in #{method.__module__}")
    version, name = match.groups()
    registered.append(Migration(version, name, method))
