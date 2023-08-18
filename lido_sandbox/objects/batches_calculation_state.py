class BatchesCalculationState:
    def __init__(
        self,
        remaining_eth_budget: int,
        finished: bool,
        batches: list[int],
        batches_length: int,
    ):
        self.remaining_eth_budget = remaining_eth_budget
        self.finished = finished
        self.batches = batches
        self.batches_length = batches_length
