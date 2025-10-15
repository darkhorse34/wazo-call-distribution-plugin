"""Security models for compliance and data protection."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class SecurityPolicy(Base):
    """Security policy model for tenant-level security settings."""
    
    __tablename__ = 'call_distributor_security_policies'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    
    # Password policy
    password_min_length = Column(Integer, default=8)
    password_require_uppercase = Column(Boolean, default=True)
    password_require_lowercase = Column(Boolean, default=True)
    password_require_numbers = Column(Boolean, default=True)
    password_require_special = Column(Boolean, default=True)
    password_max_age = Column(Integer, default=90)  # days
    password_history = Column(Integer, default=5)  # number of previous passwords to remember
    
    # Session policy
    session_timeout = Column(Integer, default=3600)  # seconds
    session_max_concurrent = Column(Integer, default=3)
    session_require_2fa = Column(Boolean, default=False)
    
    # IP policy
    ip_whitelist = Column(JSON, default=[])  # List of allowed IP ranges
    ip_blacklist = Column(JSON, default=[])  # List of blocked IP ranges
    
    # Audit policy
    audit_enabled = Column(Boolean, default=True)
    audit_retention = Column(Integer, default=365)  # days
    audit_events = Column(JSON, default=[])  # List of events to audit
    
    # PII policy
    pii_mask_enabled = Column(Boolean, default=True)
    pii_fields = Column(JSON, default=[])  # List of fields to mask
    pii_retention = Column(Integer, default=365)  # days
    
    def __repr__(self):
        return f'<SecurityPolicy(tenant_uuid={self.tenant_uuid})>'
    
    @property
    def to_dict(self):
        """Convert security policy to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'password_min_length': self.password_min_length,
            'password_require_uppercase': self.password_require_uppercase,
            'password_require_lowercase': self.password_require_lowercase,
            'password_require_numbers': self.password_require_numbers,
            'password_require_special': self.password_require_special,
            'password_max_age': self.password_max_age,
            'password_history': self.password_history,
            'session_timeout': self.session_timeout,
            'session_max_concurrent': self.session_max_concurrent,
            'session_require_2fa': self.session_require_2fa,
            'ip_whitelist': self.ip_whitelist,
            'ip_blacklist': self.ip_blacklist,
            'audit_enabled': self.audit_enabled,
            'audit_retention': self.audit_retention,
            'audit_events': self.audit_events,
            'pii_mask_enabled': self.pii_mask_enabled,
            'pii_fields': self.pii_fields,
            'pii_retention': self.pii_retention
        }

class AuditLog(Base):
    """Audit log model for security events."""
    
    __tablename__ = 'call_distributor_audit_logs'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Event details
    event_type = Column(String(64), nullable=False)
    event_category = Column(String(32), nullable=False)  # 'security', 'data', 'access'
    severity = Column(String(16), nullable=False)  # 'info', 'warning', 'critical'
    
    # Actor information
    actor_type = Column(String(32), nullable=False)  # 'user', 'system', 'agent'
    actor_id = Column(String(64), nullable=False)
    actor_ip = Column(String(45))  # IPv4/IPv6 address
    
    # Resource information
    resource_type = Column(String(32))
    resource_id = Column(String(64))
    
    # Event data
    action = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False)  # 'success', 'failure'
    details = Column(JSON)
    
    def __repr__(self):
        return f'<AuditLog(event={self.event_type}, actor={self.actor_id})>'
    
    @property
    def to_dict(self):
        """Convert audit log to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'event_category': self.event_category,
            'severity': self.severity,
            'actor_type': self.actor_type,
            'actor_id': self.actor_id,
            'actor_ip': self.actor_ip,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'action': self.action,
            'status': self.status,
            'details': self.details
        }

class ComplianceReport(Base):
    """Compliance report model for regulatory requirements."""
    
    __tablename__ = 'call_distributor_compliance_reports'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Report details
    report_type = Column(String(32), nullable=False)  # 'pii', 'security', 'audit'
    status = Column(String(16), nullable=False)  # 'compliant', 'non_compliant'
    score = Column(Integer)  # Compliance score (0-100)
    
    # Findings
    total_checks = Column(Integer, nullable=False)
    passed_checks = Column(Integer, nullable=False)
    failed_checks = Column(Integer, nullable=False)
    findings = Column(JSON)  # List of compliance findings
    
    # Remediation
    remediation_required = Column(Boolean, default=False)
    remediation_deadline = Column(DateTime)
    remediation_status = Column(String(16))  # 'pending', 'in_progress', 'completed'
    
    def __repr__(self):
        return f'<ComplianceReport(type={self.report_type}, status={self.status})>'
    
    @property
    def to_dict(self):
        """Convert compliance report to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'timestamp': self.timestamp.isoformat(),
            'report_type': self.report_type,
            'status': self.status,
            'score': self.score,
            'total_checks': self.total_checks,
            'passed_checks': self.passed_checks,
            'failed_checks': self.failed_checks,
            'findings': self.findings,
            'remediation_required': self.remediation_required,
            'remediation_deadline': self.remediation_deadline.isoformat() if self.remediation_deadline else None,
            'remediation_status': self.remediation_status
        }

class DataRetentionPolicy(Base):
    """Data retention policy model."""
    
    __tablename__ = 'call_distributor_data_retention'
    
    id = Column(Integer, primary_key=True)
    tenant_uuid = Column(String(36), nullable=False, index=True)
    
    # Policy details
    data_type = Column(String(32), nullable=False)  # 'calls', 'recordings', 'pii'
    retention_period = Column(Integer, nullable=False)  # days
    
    # Archival settings
    archive_enabled = Column(Boolean, default=False)
    archive_type = Column(String(32))  # 's3', 'local', etc.
    archive_config = Column(JSON)
    
    # Deletion settings
    secure_delete = Column(Boolean, default=True)
    delete_on_archive = Column(Boolean, default=False)
    
    # Compliance settings
    compliance_required = Column(Boolean, default=False)
    compliance_standard = Column(String(32))  # 'gdpr', 'hipaa', etc.
    
    def __repr__(self):
        return f'<DataRetentionPolicy(type={self.data_type})>'
    
    @property
    def to_dict(self):
        """Convert data retention policy to dictionary representation."""
        return {
            'id': self.id,
            'tenant_uuid': self.tenant_uuid,
            'data_type': self.data_type,
            'retention_period': self.retention_period,
            'archive_enabled': self.archive_enabled,
            'archive_type': self.archive_type,
            'archive_config': self.archive_config,
            'secure_delete': self.secure_delete,
            'delete_on_archive': self.delete_on_archive,
            'compliance_required': self.compliance_required,
            'compliance_standard': self.compliance_standard
        }
