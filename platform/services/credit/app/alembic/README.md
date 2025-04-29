## Alembic migration environment structure
Alembic is a lightweight database migration tool, used for managing and applying changes to the schema of the credit system's PostgreSQL database.

`env.py` - a Python script that is run whenever the alembic migration tool is invoked. At the very least, it contains instructions to configure and generate a SQLAlchemy engine, procure a connection from that engine along with a transaction, and then invoke the migration engine, using the connection as a source of database connectivity. The way migrations run is entirely customizable.

`script.py.mako` - a Mako template file which is used to generate new migration scripts in `versions/` directory. 

`versions/` - directory holding the individual version scripts. In Alembic, the ordering of version scripts is relative to directives within the scripts themselves, and it is theoretically possible to “splice” version files in between others, allowing migration sequences from different branches to be merged, albeit carefully by hand.


## How to add a new migration

```bash
cd src/control_plane/credit_system
make venv
source .venv-credit-system/bin/activate
cd app
alembic revision -m "<Descriptive migration name>"
```

This will create a new script in `/alembic/versions/` directory, named as `<current_date>-<revision>_<migration_name>.py`. You will need to add implementation of `upgrade()` and `downgrade()` functions.

The script must contain `revision` and `down_revision` variables - this is how Alembic knows the correct order in which to apply migrations. When we create the next revision, the new file’s `down_revision` identifier points to latest previously existing script.

To test your changes locally, you can run `make deploy_local` - this will deploy all the containers required for the application, including migration.


## Autogenerating migrations
Alembic can view the status of the database and compare it against the updated table metadata in the application, generating the “obvious” migrations, based on a comparison. 
This is achieved by adding the `--autogenerate` option to the alembic revision command, which places so-called candidate migrations into our new migrations file. **We should review and modify these by hand.**

In order to use autogeneration, start port-forwarding to the existing database, export the following env variables - `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`, and run: 

```bash
alembic revision --autogenerate -m "<Descriptive migration name>"
```