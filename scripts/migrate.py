import sys
import playhouse.migrate

import lc.config as c
import lc.model as m
import lc.migration

c.app.init_db()
m.create_tables()

meta = m.Meta.fetch()
print(f"Current schema version is: {meta.version}")

import migrations

runnable = filter(lambda m: m.version > meta.version, lc.migration.registered)

for migration in sorted(runnable, key=lambda m: m.version):
    print(f"{migration.version} - {migration.name}")
    try:
        migration.run(playhouse.migrate.SqliteMigrator(c.app.db))
    except:
        sys.exit(1)

    meta.version = migration.version
    meta.save()
