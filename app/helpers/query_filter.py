
class QueryFilter(object) :
    def __init__(self, operators) :
        self.__operators = operators

    def assignOperatorToFilters(self, filters, operator) :
        pass

    def is_not_defined_operator(self, operator) :
        return self.__operators.count(operator) <= 0

    def is_defined_operator(self, operator) :
        return self.__operators.count(operator) > 0

class MongoQueryFilter(QueryFilter) :
    def __init__(self) :
        mongo_operators = [
            'ne', 'lt', 'lte', 'gt', 'gte', 'not', 'in', 'nin', 'mod', 
            'all', 'size', 'exists', 'exact', 'iexact', 
            'contains', 'icontains', 'startswith', 'istartswith', 
            'endswith', 'iendswith', 'match'
        ]
        QueryFilter.__init__(self, mongo_operators)

    def assignOperatorToFilters(self, filters, operator) :
        if self.is_not_defined_operator(operator) :
            Exception('InvalidQueryOperatorError')

        newFilters = []
        for f in filters :
            newFilters.append({ 
                'field': f['field'] + '__' + operator, 
                'value': f['value'] 
            })

        return newFilters