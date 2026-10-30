# app/tests/unitary/helpers_test.py

import json
import unittest

from flask import Flask

from app.helpers.error_helpers import RegisterNotFound, CSTM_Exception, handleNotFound
from app.helpers.query_filter import MongoQueryFilter


class QueryFilterTest(unittest.TestCase):

    def test_assigns_operator(self):
        filters = [{'field': 'title', 'value': 'abc'}, {'field': 'tag', 'value': '1'}]
        self.assertEqual(MongoQueryFilter().assignOperatorToFilters(filters, 'icontains'), [
            {'field': 'title__icontains', 'value': 'abc'},
            {'field': 'tag__icontains', 'value': '1'}])

    def test_rejects_unknown_operator(self):
        with self.assertRaises(ValueError):
            MongoQueryFilter().assignOperatorToFilters([{'field': 'x', 'value': 1}], 'drop')

    def test_operator_checks(self):
        queryFilter = MongoQueryFilter()
        self.assertTrue(queryFilter.is_defined_operator('gte'))
        self.assertTrue(queryFilter.is_not_defined_operator('$where'))


class ErrorHelpersTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)

    def test_register_not_found_response(self):
        with self.app.app_context():
            res = handleNotFound(RegisterNotFound("Record not found", payload={"recordId": "1"}))
        self.assertEqual(res.status_code, 404)
        self.assertEqual(json.loads(res.data), {"recordId": "1", "message": "Record not found"})

    def test_custom_exception_with_entity_and_status(self):
        with self.app.app_context():
            res = handleNotFound(CSTM_Exception("En uso", status_code=419, entity="Project"))
        self.assertEqual(res.status_code, 419)
        self.assertEqual(json.loads(res.data), {"message": "En uso", "entity": "Project"})


if __name__ == "__main__":
    unittest.main()
