"""Custom exceptions for the call distributor plugin."""

class CallDistributorError(Exception):
    """Base exception for call distributor errors."""
    pass

class QueueNotFound(CallDistributorError):
    """Raised when a queue is not found."""
    def __init__(self, queue_id):
        super().__init__(f"Queue {queue_id} not found")
        self.queue_id = queue_id

class InvalidQueueStrategy(CallDistributorError):
    """Raised when an invalid queue strategy is provided."""
    pass

class AgentNotFound(CallDistributorError):
    """Raised when an agent is not found."""
    def __init__(self, agent_id):
        super().__init__(f"Agent {agent_id} not found")
        self.agent_id = agent_id

class QueueMemberNotFound(CallDistributorError):
    """Raised when a queue member is not found."""
    def __init__(self, member_id):
        super().__init__(f"Queue member {member_id} not found")
        self.member_id = member_id

class ScheduleNotFound(CallDistributorError):
    """Raised when a schedule is not found."""
    def __init__(self, schedule_id):
        super().__init__(f"Schedule {schedule_id} not found")
        self.schedule_id = schedule_id

class InvalidSkillLevel(CallDistributorError):
    """Raised when an invalid skill level is provided."""
    def __init__(self, skill_level):
        super().__init__(f"Invalid skill level: {skill_level}. Must be between 0 and 100")
        self.skill_level = skill_level

class UnauthorizedTenant(CallDistributorError):
    """Raised when a tenant is not authorized to access a resource."""
    def __init__(self, tenant_uuid):
        super().__init__(f"Tenant {tenant_uuid} is not authorized to access this resource")
        self.tenant_uuid = tenant_uuid

class InvalidConfiguration(CallDistributorError):
    """Raised when invalid configuration is provided."""
    pass

class ServiceUnavailable(CallDistributorError):
    """Raised when a required service is unavailable."""
    def __init__(self, service_name):
        super().__init__(f"Service {service_name} is unavailable")
        self.service_name = service_name
