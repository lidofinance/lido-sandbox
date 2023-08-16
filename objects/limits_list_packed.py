class LimitsListPacked:
    def __init__(
        self,
        churn_validators_per_day_limit: int,
        one_off_cl_balance_decrease_bp_limit: int,
        annual_balance_increase_bp_limit: int,
        simulated_share_rate_deviation_bp_limit: int,
        max_validator_exit_requests_per_report: int,
        max_accounting_extra_data_list_items_count: int,
        max_node_operators_per_extra_data_item_count: int,
        request_timestamp_margin: int,
        max_positive_token_rebase: int,
    ):
        self.churn_validators_per_day_limit = churn_validators_per_day_limit
        self.one_off_cl_balance_decrease_bp_limit = one_off_cl_balance_decrease_bp_limit
        self.annual_balance_increase_bp_limit = annual_balance_increase_bp_limit
        self.simulated_share_rate_deviation_bp_limit = simulated_share_rate_deviation_bp_limit
        self.max_validator_exit_requests_per_report = max_validator_exit_requests_per_report
        self.max_accounting_extra_data_list_items_count = max_accounting_extra_data_list_items_count
        self.max_node_operators_per_extra_data_item_count = (
            max_node_operators_per_extra_data_item_count
        )
        self.request_timestamp_margin = request_timestamp_margin
        self.max_positive_token_rebase = max_positive_token_rebase
