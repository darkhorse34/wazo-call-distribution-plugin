"""Plugin entry point for the call distributor."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from flask import g, request

from .api.queue import bp as queue_bp
from .api.distribution import bp as distribution_bp
from .api.agent import bp as agent_bp
from .api.policy import bp as policy_bp
from .api.schedule import bp as schedule_bp
from .api.media import bp as media_bp
from .api.call_control import bp as call_control_bp
from .api.event import bp as event_bp
from .api.desktop import bp as desktop_bp
from .api.supervisor import bp as supervisor_bp
from .api.callback import bp as callback_bp
from .api.rbac import bp as rbac_bp
from .api.reporting import bp as reporting_bp
from .api.integration import bp as integration_bp
from .api.reliability import bp as reliability_bp
from .websocket import WebSocketHandler
from .models import Base

logger = logging.getLogger(__name__)

class Plugin:
    """Call distributor plugin for wazo-calld."""
    
    def __init__(self):
        self.session = None
        self.websocket_handler = None
    
    def load(self, app_or_deps):
        """Load the plugin."""
        app = app_or_deps.get("app") if isinstance(app_or_deps, dict) else app_or_deps
        
        # Initialize database
        config = app.config['call_distributor']
        engine = create_engine(config['db_connection'])
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        self.session = scoped_session(session_factory)
        
        # Register database session middleware
        @app.before_request
        def before_request():
            request.db_session = self.session()
        
        @app.teardown_request
        def teardown_request(exception=None):
            if hasattr(request, 'db_session'):
                if exception:
                    request.db_session.rollback()
                request.db_session.close()
        
        # Register blueprints
        app.register_blueprint(queue_bp, url_prefix="/api/calld/1.0/queues")
        app.register_blueprint(distribution_bp, url_prefix="/api/calld/1.0")
        app.register_blueprint(agent_bp, url_prefix="/api/calld/1.0/agents")
        app.register_blueprint(policy_bp, url_prefix="/api/calld/1.0/policies")
        app.register_blueprint(schedule_bp, url_prefix="/api/calld/1.0/schedules")
        app.register_blueprint(media_bp, url_prefix="/api/calld/1.0")
        app.register_blueprint(call_control_bp, url_prefix="/api/calld/1.0")
        app.register_blueprint(event_bp, url_prefix="/api/calld/1.0/events")
        app.register_blueprint(desktop_bp, url_prefix="/api/calld/1.0/desktop")
        app.register_blueprint(supervisor_bp, url_prefix="/api/calld/1.0/supervisor")
        app.register_blueprint(callback_bp, url_prefix="/api/calld/1.0/callbacks")
        app.register_blueprint(rbac_bp, url_prefix="/api/calld/1.0/rbac")
        app.register_blueprint(reporting_bp, url_prefix="/api/calld/1.0/reporting")
        app.register_blueprint(integration_bp, url_prefix="/api/calld/1.0/integrations")
        app.register_blueprint(reliability_bp, url_prefix="/api/calld/1.0/reliability")
        
        # Initialize WebSocket handler
        self.websocket_handler = WebSocketHandler(app.config['call_distributor']['redis_url'])
        
        logger.info("Call distributor plugin loaded")
