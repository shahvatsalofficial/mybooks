def parallel_scatter_gather_reducer(current_list: List[str], new_items: List[str]) -> List[str]:
    return current_list + [item for item in new_items if item not in current_list]
