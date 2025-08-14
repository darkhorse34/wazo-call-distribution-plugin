# Loaded by wazo-calld via stevedore using entry_points: wazo_calld.plugins
# We keep it tiny: register a Flask blueprint under /api/calld/1.0

from .api import bp as blueprint

class Plugin:
    # Most recent wazo-calld expects `load(self, app)` (Flask) signature
    # If your build passes a dict with deps instead, app will still be there as deps["app"].
    def load(self, app_or_deps):
        app = app_or_deps.get("app") if isinstance(app_or_deps, dict) else app_or_deps
        app.register_blueprint(blueprint, url_prefix="/api/calld/1.0")
