
from lc.migration import migration

# This migration just ensures that the meta table is updated to version 1

@migration
def run(m):
    pass
