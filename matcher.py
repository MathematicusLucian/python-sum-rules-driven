def select_by_condition(items, predicate):
    return [item for item in items if predicate(item)]

def select_by_attributes(items, allowed):
    return [item for item in items if item in allowed]

def count_items(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    animal_list = ['wolf', 'cat', 'wolf pack', 'wolf', 'wolves', 'wolf'] 

    print(select_by_condition(animal_list, lambda x: 'wol' in x))                   # ['wolf', 'wolf pack', 'wolf', 'wolves', 'wolf']
    print(select_by_condition(animal_list, lambda x: x in {'wolf', 'wolves'}))      # ['wolf', 'wolf', 'wolves', 'wolf']
    print(select_by_attributes(animal_list, {'wolf'}))                              # ['wolf', 'wolf', 'wolf']
    print(select_by_attributes(animal_list, {'wolf', 'wolves'}))                    # ['wolf', 'wolf', 'wolves', 'wolf']
    print(count_items(animal_list))                                                 # {'wolf': 3, 'cat': 1, 'wolf pack': 1, 'wolves': 1}

