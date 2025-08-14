from flask import Blueprint, request, jsonify, current_app
from .service import DistributorService

bp = Blueprint("call_distributor", __name__)
svc = DistributorService()

def _token_from_headers():
    # Accept either X-Auth-Token (classic) or Authorization: Bearer <token>
    h = request.headers
    if "X-Auth-Token" in h:
        return h["X-Auth-Token"]
    auth = h.get("Authorization", "")
    return auth.replace("Bearer ", "").strip() if auth.startswith("Bearer ") else None

@bp.route("/csr/route-call", methods=["POST"])
def route_call():
    """
    Sequential distribution: try each agent user_uuid until one answers.
    Body:
    {
      "caller_call_id": "1446422660.20",
      "agent_user_uuids": ["<uuid-1006>", "<uuid-1007>"],
      "ring_timeout": 15   // optional overrides default
    }
    """
    token = _token_from_headers()
    body = request.get_json(force=True)
    res = svc.sequential_connect(
        token=token,
        caller_call_id=body["caller_call_id"],
        agent_user_uuids=body["agent_user_uuids"],
        ring_timeout=body.get("ring_timeout"),
    )
    return jsonify(res), 200

@bp.route("/csr/transfer-to-survey", methods=["POST"])
def transfer_to_survey():
    """
    Blind-transfer the live caller leg to the survey destination.
    Body:
    {
      "call_id": "1446422660.20",
      "context": "default",   // optional (falls back to config)
      "exten": "8899",        // optional (falls back to config)
      "timeout": 15           // optional
    }
    """
    token = _token_from_headers()
    body = request.get_json(force=True)
    res = svc.transfer_to_survey(
        token=token,
        call_id=body["call_id"],
        context=body.get("context"),
        exten=body.get("exten"),
        timeout=body.get("timeout"),
    )
    return jsonify(res), 200

@bp.route("/csr/ping", methods=["GET"])
def ping():
    # simple health for debugging in your logs
    return jsonify({"ok": True}), 200
