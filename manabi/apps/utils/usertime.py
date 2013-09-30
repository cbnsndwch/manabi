from account.models import Account
import pytz
from settings import START_OF_DAY
import datetime


def start_and_end_of_day(user, date=None):
    '''
    `date` is a datetime.date object.

    Returns a tuple of 2 UTC datetimes.

    Takes the user's preferred start of day (usually a default of 4am) into account.
    '''
    account = Account.objects.get(user=user)
    timezone = pytz.timezone(unicode(account.timezone))

    if date is None:
        # Today
        date = datetime.datetime.now(timezone).date()


    start = datetime.datetime.combine(date, datetime.time(
        hour=START_OF_DAY, minute=0, second=0, tzinfo=timezone)
        ).astimezone(pytz.utc)

    #start = datetime.datetime.now(timezone).replace(
    #    hour=START_OF_DAY, minute=0, second=0).astimezone(pytz.utc)
    
    end = start + datetime.timedelta(hours=23, minutes=59, seconds=59)

    return (start, end,)


