import time
from typing import List, Optional
from flask import current_app
from wazo_calld_client import Client as CalldClient

def _conf():
    # read our plugin config injected by wazo-calld (Flask app config)
    # accessible at current_app.config["call_distributor"]
    return current_app.config.get("call_distributor", {}) or {}

def _client(token: str) -> CalldClient:
    # calld is serving this very process; loopback to the same API
    # Hostname is fine; TLS verification follows your stack config.
    return CalldClient("localhost", token=token, verify_certificate=False)

class DistributorService:
    def sequential_connect(
        self,
        token: str,
        caller_call_id: str,
        agent_user_uuids: List[str],
        ring_timeout: Optional[int] = None,
    ):
        """
        Try each agent (by user_uuid) with connect_user() until one answers.
        If nobody answers, we leave the original call alone.
        Returns a small status dict you can display in your UI.
        """
        cfg = _conf()
        ring_timeout = int(ring_timeout or cfg.get("ring_timeout", 15))
        c = _client(token)

        tried = []
        for user_uuid in agent_user_uuids:
            tried.append(user_uuid)
            # Connect the existing caller call to an agent user
            # This uses the authenticated token's tenant to locate the user
            c.calls.connect_user(caller_call_id, user_uuid, timeout=ring_timeout)

            # Poll a bit to see if the call bridged/talking_to changed
            # In real life you'd subscribe to events; polling is simple for a first cut
            t_end = time.time() + ring_timeout + 1
            while time.time() < t_end:
                call = c.calls.get_call(caller_call_id)
                if call.get("talking_to"):
                    return {
                        "connected": True,
                        "agent_user_uuid": user_uuid,
                        "tried": tried,
                    }
                time.sleep(0.5)

            # No answer, cancel any pending transfer for safety and move on
            # (connect_user returns immediately; timeout governs agent ringing)
            # There isn't a specific "cancel" for connect_user; just continue.
            continue

        return {"connected": False, "tried": tried}

    def transfer_to_survey(
        self,
        token: str,
        call_id: str,
        context: Optional[str] = None,
        exten: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        cfg = _conf()
        context = context or cfg.get("survey_context", "default")
        exten = exten or cfg.get("survey_exten", "8899")
        timeout = int(timeout or cfg.get("survey_timeout", 15))

        c = _client(token)
        # We blind-transfer the caller leg to the survey destination
        transfer = c.transfers.make_transfer(
            transferred=call_id,
            initiator=call_id,
            context=context,
            exten=exten,
            flow="blind",
            timeout=timeout,
            variables={},  # add your own flags if needed
        )
        return {"transfer_id": transfer["id"], "to": {"context": context, "exten": exten}}
