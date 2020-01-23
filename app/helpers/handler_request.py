# app/helpers/handler_request.py


def getQueryParams(request):
    if request.args:
        filters = []
        for key in request.args.keys():
            filters.append({"field":key, "value":request.args.get(key)})
        return filters
    return None