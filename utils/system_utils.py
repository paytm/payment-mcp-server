import datetime

class DateService:
    @staticmethod
    def get_current_date() -> str:
        # Create IST timezone once
        ist_timezone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        ist_time = datetime.datetime.now(ist_timezone)
        return ist_time.strftime('%Y-%m-%dT%H:%M:%S+05:30')
    
    @staticmethod
    def get_date_by_time_range(time_range: str) -> str:
        # Create IST timezone once
        ist_timezone = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        # Calculate date directly in IST timezone
        ist_date = datetime.datetime.now(ist_timezone) - datetime.timedelta(days=int(time_range))
        return ist_date.strftime('%Y-%m-%dT%H:%M:%S+05:30')