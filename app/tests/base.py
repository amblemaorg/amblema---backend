# -*- coding: utf-8 -*-
# app/tests/base.py

from instance.config import assert_testing_database


def drop_testing_database(db):
    """Borra la base de pruebas actual, solo si su nombre termina en _testing."""
    database = db.connection.get_default_database()
    assert_testing_database("mongodb://host/{}".format(database.name))
    db.connection.drop_database(database.name)
