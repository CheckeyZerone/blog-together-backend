import datetime
import pytz


async def get_now_datetime_async(timezone=pytz.timezone("Etc/GMT-8")):
    return datetime.datetime.now(tz=timezone)