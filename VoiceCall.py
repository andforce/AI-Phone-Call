class VoiceCall:
    VOICE_CALL_RING = "RING"
    VOICE_CALL_CLIP = "CLIP"
    VOICE_CALL_BEGIN = "CALL_BEGIN"
    VOICE_CALL_END = "CALL_END"
    VOICE_CALL_NO_CARRIER = "NO_CARRIER"
    VOICE_CALL_MISSED = "MISSED_CALL"
    VOICE_CALL_SAY_HELLO_DONE = "SAY_HELLO_DONE"

    def __init__(self, status, phone_number: str = None, ring_count: int = 0):
        self.status = status
        self.phone_number: str = phone_number
        self.ring_count: int = ring_count
