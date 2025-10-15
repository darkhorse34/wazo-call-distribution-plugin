"""Schedule service for managing business hours and holidays."""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, time
from sqlalchemy.orm import Session
from ..models import Schedule, TimeRange, Holiday
from ..exceptions import ScheduleNotFound

class ScheduleService:
    """Service for managing schedules and calendars."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get(self, schedule_id: int, tenant_uuid: str) -> Schedule:
        """Get a schedule by ID and tenant."""
        schedule = self.session.query(Schedule).filter(
            Schedule.id == schedule_id,
            Schedule.tenant_uuid == tenant_uuid
        ).first()
        
        if not schedule:
            raise ScheduleNotFound(schedule_id)
        
        return schedule
    
    def list(self, tenant_uuid: str) -> List[Schedule]:
        """List all schedules for a tenant."""
        return self.session.query(Schedule).filter(
            Schedule.tenant_uuid == tenant_uuid
        ).all()
    
    def create(self, tenant_uuid: str, schedule_data: Dict) -> Schedule:
        """Create a new schedule."""
        schedule = Schedule(tenant_uuid=tenant_uuid)
        self._update_schedule_data(schedule, schedule_data)
        
        self.session.add(schedule)
        self.session.commit()
        
        return schedule
    
    def update(self, schedule_id: int, tenant_uuid: str, schedule_data: Dict) -> Schedule:
        """Update an existing schedule."""
        schedule = self.get(schedule_id, tenant_uuid)
        self._update_schedule_data(schedule, schedule_data)
        
        self.session.commit()
        return schedule
    
    def delete(self, schedule_id: int, tenant_uuid: str) -> None:
        """Delete a schedule."""
        schedule = self.get(schedule_id, tenant_uuid)
        self.session.delete(schedule)
        self.session.commit()
    
    def _update_schedule_data(self, schedule: Schedule, data: Dict) -> None:
        """Update schedule with provided data."""
        # Update basic fields
        schedule.name = data.get('name', schedule.name)
        schedule.description = data.get('description', schedule.description)
        schedule.fallback_type = data.get('fallback_type', schedule.fallback_type)
        schedule.fallback_destination = data.get('fallback_destination', schedule.fallback_destination)
        
        # Update time ranges
        if 'time_ranges' in data:
            # Remove existing time ranges
            for tr in schedule.time_ranges:
                self.session.delete(tr)
            
            # Add new time ranges
            for tr_data in data['time_ranges']:
                tr = TimeRange(
                    schedule=schedule,
                    day_start=tr_data['day_start'],
                    day_end=tr_data['day_end'],
                    time_start=datetime.strptime(tr_data['time_start'], '%H:%M').time(),
                    time_end=datetime.strptime(tr_data['time_end'], '%H:%M').time()
                )
                self.session.add(tr)
        
        # Update holidays
        if 'holidays' in data:
            # Remove existing holidays
            for holiday in schedule.holidays:
                self.session.delete(holiday)
            
            # Add new holidays
            for h_data in data['holidays']:
                holiday = Holiday(
                    schedule=schedule,
                    name=h_data['name'],
                    date=date.fromisoformat(h_data['date']),
                    recurring=h_data.get('recurring', False)
                )
                
                if 'time_start' in h_data:
                    holiday.time_start = datetime.strptime(h_data['time_start'], '%H:%M').time()
                if 'time_end' in h_data:
                    holiday.time_end = datetime.strptime(h_data['time_end'], '%H:%M').time()
                
                self.session.add(holiday)
    
    def check_schedule_status(self, schedule_id: int, tenant_uuid: str,
                            check_time: Optional[datetime] = None) -> Tuple[bool, Optional[str]]:
        """Check if schedule is currently open and get fallback if closed."""
        schedule = self.get(schedule_id, tenant_uuid)
        check_time = check_time or datetime.now()
        
        # Check holidays first
        for holiday in schedule.holidays:
            if self._is_holiday_active(holiday, check_time):
                return False, self._get_fallback_destination(schedule)
        
        # Check time ranges
        for time_range in schedule.time_ranges:
            if self._is_time_range_active(time_range, check_time):
                return True, None
        
        return False, self._get_fallback_destination(schedule)
    
    def _is_holiday_active(self, holiday: Holiday, check_time: datetime) -> bool:
        """Check if a holiday is active at the given time."""
        check_date = check_time.date()
        
        # Check if date matches (considering recurring)
        if holiday.recurring:
            if check_date.month == holiday.date.month and check_date.day == holiday.date.day:
                if not holiday.time_start:
                    return True
                return self._is_time_in_range(check_time.time(),
                                            holiday.time_start,
                                            holiday.time_end)
        else:
            if check_date == holiday.date:
                if not holiday.time_start:
                    return True
                return self._is_time_in_range(check_time.time(),
                                            holiday.time_start,
                                            holiday.time_end)
        
        return False
    
    def _is_time_range_active(self, time_range: TimeRange, check_time: datetime) -> bool:
        """Check if a time range is active at the given time."""
        weekday = check_time.weekday()
        
        # Check if day is in range
        if not time_range.day_start <= weekday <= time_range.day_end:
            return False
        
        # Check if time is in range
        return self._is_time_in_range(check_time.time(),
                                    time_range.time_start,
                                    time_range.time_end)
    
    def _is_time_in_range(self, check_time: time,
                         start_time: time, end_time: time) -> bool:
        """Check if a time is within a range."""
        if start_time <= end_time:
            return start_time <= check_time <= end_time
        else:  # Handle overnight ranges
            return check_time >= start_time or check_time <= end_time
    
    def _get_fallback_destination(self, schedule: Schedule) -> Optional[str]:
        """Get fallback destination for closed schedule."""
        if schedule.fallback_type and schedule.fallback_destination:
            return f"{schedule.fallback_type}:{schedule.fallback_destination}"
        return None
