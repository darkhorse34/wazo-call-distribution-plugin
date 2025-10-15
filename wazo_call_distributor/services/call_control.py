"""Call control service for realtime call operations."""

from typing import Dict, Optional
from wazo_calld_client import Client as CalldClient
from ..exceptions import ServiceUnavailable

class CallControlService:
    """Service for realtime call control operations."""
    
    def __init__(self, calld_client: CalldClient):
        self.calld = calld_client
    
    def transfer_call(self, call_id: str, destination: str,
                     flow: str = 'blind') -> Dict:
        """Transfer a call to another destination.
        
        Args:
            call_id: The ID of the call to transfer
            destination: The transfer destination (extension or number)
            flow: The transfer type ('blind' or 'attended')
        """
        try:
            if flow == 'blind':
                return self.calld.transfers.make_transfer(
                    call_id,
                    destination,
                    flow='blind'
                )
            else:
                return self.calld.transfers.make_transfer(
                    call_id,
                    destination,
                    flow='attended'
                )
        except Exception as e:
            raise ServiceUnavailable(f"Failed to transfer call: {str(e)}")
    
    def hold_call(self, call_id: str) -> Dict:
        """Put a call on hold."""
        try:
            return self.calld.calls.hold(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to hold call: {str(e)}")
    
    def resume_call(self, call_id: str) -> Dict:
        """Resume a held call."""
        try:
            return self.calld.calls.resume(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to resume call: {str(e)}")
    
    def mute_call(self, call_id: str) -> Dict:
        """Mute a call."""
        try:
            return self.calld.calls.mute(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to mute call: {str(e)}")
    
    def unmute_call(self, call_id: str) -> Dict:
        """Unmute a call."""
        try:
            return self.calld.calls.unmute(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to unmute call: {str(e)}")
    
    def start_recording(self, call_id: str) -> Dict:
        """Start recording a call."""
        try:
            return self.calld.calls.start_record(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to start recording: {str(e)}")
    
    def stop_recording(self, call_id: str) -> Dict:
        """Stop recording a call."""
        try:
            return self.calld.calls.stop_record(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to stop recording: {str(e)}")
    
    def whisper(self, call_id: str, supervisor_id: str) -> Dict:
        """Start whisper coaching on a call."""
        try:
            return self.calld.calls.start_whisper(
                call_id,
                supervisor_id
            )
        except Exception as e:
            raise ServiceUnavailable(f"Failed to start whisper: {str(e)}")
    
    def stop_whisper(self, call_id: str, supervisor_id: str) -> Dict:
        """Stop whisper coaching on a call."""
        try:
            return self.calld.calls.stop_whisper(
                call_id,
                supervisor_id
            )
        except Exception as e:
            raise ServiceUnavailable(f"Failed to stop whisper: {str(e)}")
    
    def barge(self, call_id: str, supervisor_id: str) -> Dict:
        """Barge into a call."""
        try:
            return self.calld.calls.start_barge(
                call_id,
                supervisor_id
            )
        except Exception as e:
            raise ServiceUnavailable(f"Failed to start barge: {str(e)}")
    
    def stop_barge(self, call_id: str, supervisor_id: str) -> Dict:
        """Stop barging into a call."""
        try:
            return self.calld.calls.stop_barge(
                call_id,
                supervisor_id
            )
        except Exception as e:
            raise ServiceUnavailable(f"Failed to stop barge: {str(e)}")
    
    def pickup_call(self, call_id: str, interceptor_id: str) -> Dict:
        """Pick up a ringing call."""
        try:
            return self.calld.calls.pickup(
                call_id,
                interceptor_id
            )
        except Exception as e:
            raise ServiceUnavailable(f"Failed to pickup call: {str(e)}")
    
    def get_call_status(self, call_id: str) -> Optional[Dict]:
        """Get current status of a call."""
        try:
            return self.calld.calls.get_call(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to get call status: {str(e)}")
    
    def list_active_calls(self) -> Dict:
        """List all active calls."""
        try:
            return self.calld.calls.list_calls()
        except Exception as e:
            raise ServiceUnavailable(f"Failed to list calls: {str(e)}")
    
    def hangup_call(self, call_id: str) -> None:
        """Hang up a call."""
        try:
            self.calld.calls.hangup(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to hangup call: {str(e)}")
    
    def play_sound(self, call_id: str, sound_file: str) -> Dict:
        """Play a sound file on a call."""
        try:
            return self.calld.calls.play_sound(
                call_id,
                sound_file
            )
        except Exception as e:
            raise ServiceUnavailable(f"Failed to play sound: {str(e)}")
    
    def stop_sound(self, call_id: str) -> Dict:
        """Stop playing sound on a call."""
        try:
            return self.calld.calls.stop_sound(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to stop sound: {str(e)}")
    
    def send_dtmf(self, call_id: str, digits: str) -> Dict:
        """Send DTMF digits on a call."""
        try:
            return self.calld.calls.send_dtmf(
                call_id,
                digits
            )
        except Exception as e:
            raise ServiceUnavailable(f"Failed to send DTMF: {str(e)}")
    
    def answer_call(self, call_id: str) -> Dict:
        """Answer a ringing call."""
        try:
            return self.calld.calls.answer(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to answer call: {str(e)}")
    
    def reject_call(self, call_id: str) -> Dict:
        """Reject a ringing call."""
        try:
            return self.calld.calls.reject(call_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to reject call: {str(e)}")
    
    def cancel_transfer(self, transfer_id: str) -> None:
        """Cancel an ongoing transfer."""
        try:
            self.calld.transfers.cancel_transfer(transfer_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to cancel transfer: {str(e)}")
    
    def complete_transfer(self, transfer_id: str) -> Dict:
        """Complete an attended transfer."""
        try:
            return self.calld.transfers.complete_transfer(transfer_id)
        except Exception as e:
            raise ServiceUnavailable(f"Failed to complete transfer: {str(e)}")
