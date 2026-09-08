import datetime
from app.models.school_year_model import SchoolYear

def get_school_year_date_filters():
    active_school_year = SchoolYear.objects(isDeleted=False, status="1").first()
    start_date = None
    if active_school_year and active_school_year.startDate:
        start_date = datetime.datetime.combine(active_school_year.startDate, datetime.time.min)
    
    filters = []
    if start_date:
        filters.append({"field": "createdAt__gte", "value": start_date})
    return filters

