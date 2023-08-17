class Checkpoint:
    def __init__(self, from_request_id: int = 0, max_share_rate: int = 0):
        self.from_request_id = from_request_id
        self.max_share_rate = max_share_rate
