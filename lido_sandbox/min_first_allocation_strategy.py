class MinFirstAllocationStrategy:
    MAX_UINT256 = 2**256 - 1

    @staticmethod
    def ceildiv(a: int, b: int) -> int:
        return -(a // -b)

    @staticmethod
    def allocate(
        buckets: list[int], capacities: list[int], allocation_size: int
    ) -> int:
        allocated = 0
        while allocated < allocation_size:
            allocated_to_best_candidate = (
                MinFirstAllocationStrategy.allocate_to_best_candidate(
                    buckets, capacities, allocation_size - allocated
                )
            )
            if allocated_to_best_candidate == 0:
                break
            allocated += allocated_to_best_candidate
        return allocated

    @staticmethod
    def allocate_to_best_candidate(
        buckets: list[int], capacities: list[int], allocation_size: int
    ) -> int:
        best_candidate_index = len(buckets)
        best_candidate_allocation = MinFirstAllocationStrategy.MAX_UINT256
        best_candidates_count = 0

        if allocation_size == 0:
            return 0

        for i in range(len(buckets)):
            if buckets[i] >= capacities[i]:
                continue
            elif best_candidate_allocation > buckets[i]:
                best_candidate_index = i
                best_candidates_count = 1
                best_candidate_allocation = buckets[i]
            elif best_candidate_allocation == buckets[i]:
                best_candidates_count += 1

        if best_candidates_count == 0:
            return 0

        allocation_size_upper_bound = MinFirstAllocationStrategy.MAX_UINT256
        for j in range(len(buckets)):
            if buckets[j] >= capacities[j]:
                continue
            elif (
                buckets[j] > best_candidate_allocation
                and buckets[j] < allocation_size_upper_bound
            ):
                allocation_size_upper_bound = buckets[j]

        allocated = min(
            MinFirstAllocationStrategy.ceildiv(allocation_size, best_candidates_count)
            if best_candidates_count > 1
            else allocation_size,
            min(allocation_size_upper_bound, capacities[best_candidate_index])
            - best_candidate_allocation,
        )
        buckets[best_candidate_index] += allocated
        return allocated
