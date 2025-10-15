"""Desktop service for agent interface."""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import AgentDesktopSettings, WrapUpCode, CallNote, Agent
from ..exceptions import AgentNotFound

class DesktopService:
    """Service for managing agent desktop features."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_agent_settings(self, agent_id: int, tenant_uuid: str) -> AgentDesktopSettings:
        """Get agent desktop settings."""
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        if not agent.desktop_settings:
            # Create default settings if none exist
            settings = AgentDesktopSettings(
                agent_id=agent_id,
                tenant_uuid=tenant_uuid
            )
            self.session.add(settings)
            self.session.commit()
            return settings
        
        return agent.desktop_settings
    
    def update_agent_settings(self, agent_id: int, tenant_uuid: str,
                            settings_data: Dict) -> AgentDesktopSettings:
        """Update agent desktop settings."""
        settings = self.get_agent_settings(agent_id, tenant_uuid)
        
        for key, value in settings_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        self.session.commit()
        return settings
    
    def get_wrap_up_codes(self, tenant_uuid: str,
                         category: Optional[str] = None) -> List[WrapUpCode]:
        """Get wrap-up codes for a tenant."""
        query = self.session.query(WrapUpCode).filter(
            WrapUpCode.tenant_uuid == tenant_uuid
        )
        
        if category:
            query = query.filter(WrapUpCode.category == category)
        
        return query.all()
    
    def create_wrap_up_code(self, tenant_uuid: str,
                           code_data: Dict) -> WrapUpCode:
        """Create a new wrap-up code."""
        code = WrapUpCode(tenant_uuid=tenant_uuid, **code_data)
        self.session.add(code)
        self.session.commit()
        return code
    
    def update_wrap_up_code(self, code_id: int, tenant_uuid: str,
                           code_data: Dict) -> WrapUpCode:
        """Update an existing wrap-up code."""
        code = self.session.query(WrapUpCode).filter(
            WrapUpCode.id == code_id,
            WrapUpCode.tenant_uuid == tenant_uuid
        ).first()
        
        if not code:
            raise ValueError(f"Wrap-up code {code_id} not found")
        
        for key, value in code_data.items():
            setattr(code, key, value)
        
        self.session.commit()
        return code
    
    def delete_wrap_up_code(self, code_id: int, tenant_uuid: str) -> None:
        """Delete a wrap-up code."""
        code = self.session.query(WrapUpCode).filter(
            WrapUpCode.id == code_id,
            WrapUpCode.tenant_uuid == tenant_uuid
        ).first()
        
        if code:
            self.session.delete(code)
            self.session.commit()
    
    def add_call_note(self, agent_id: int, tenant_uuid: str,
                      note_data: Dict) -> CallNote:
        """Add a note to a call."""
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        note = CallNote(
            agent_id=agent_id,
            tenant_uuid=tenant_uuid,
            timestamp=datetime.utcnow().isoformat(),
            **note_data
        )
        
        self.session.add(note)
        self.session.commit()
        return note
    
    def get_call_notes(self, call_id: str, tenant_uuid: str) -> List[CallNote]:
        """Get all notes for a call."""
        return self.session.query(CallNote).filter(
            CallNote.call_id == call_id,
            CallNote.tenant_uuid == tenant_uuid
        ).order_by(CallNote.timestamp.desc()).all()
    
    def get_agent_call_history(self, agent_id: int, tenant_uuid: str,
                             limit: int = 50) -> List[Dict]:
        """Get call history for an agent."""
        notes = self.session.query(CallNote).filter(
            CallNote.agent_id == agent_id,
            CallNote.tenant_uuid == tenant_uuid
        ).order_by(CallNote.timestamp.desc()).limit(limit).all()
        
        return [note.to_dict for note in notes]
    
    def update_call_note(self, note_id: int, tenant_uuid: str,
                        note_data: Dict) -> CallNote:
        """Update an existing call note."""
        note = self.session.query(CallNote).filter(
            CallNote.id == note_id,
            CallNote.tenant_uuid == tenant_uuid
        ).first()
        
        if not note:
            raise ValueError(f"Call note {note_id} not found")
        
        for key, value in note_data.items():
            setattr(note, key, value)
        
        self.session.commit()
        return note
    
    def delete_call_note(self, note_id: int, tenant_uuid: str) -> None:
        """Delete a call note."""
        note = self.session.query(CallNote).filter(
            CallNote.id == note_id,
            CallNote.tenant_uuid == tenant_uuid
        ).first()
        
        if note:
            self.session.delete(note)
            self.session.commit()
    
    def get_agent_kpis(self, agent_id: int, tenant_uuid: str) -> Dict:
        """Get personal KPIs for an agent."""
        agent = self.session.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_uuid == tenant_uuid
        ).first()
        
        if not agent:
            raise AgentNotFound(agent_id)
        
        # TODO: Implement KPI calculation using metrics data
        return {
            'calls_handled': 0,
            'average_handle_time': 0,
            'average_wrap_up_time': 0,
            'service_level': 0,
            'customer_satisfaction': 0
        }
