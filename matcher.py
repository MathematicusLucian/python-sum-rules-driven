# [a for i, a in enumerate(animal_list) if 'wol' in a]
def select_by_condition(items, predicate):
    return [item for item in enumerate(items) if predicate(item)]

# [a for i, a in enumerate(animal_list) if a in {'wolf', 'wolves'}]
def select_by_condition(items, predicate):
    return [item for i, item in enumerate(items) if predicate(item)]

def count_items(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


animal_list = ['wolf', 'cat', 'wolf pack', 'wolf', 'wolves', 'wolf'] 

print(select_by_condition(animal_list, lambda x: 'wol' in x))
print(select_by_condition(animal_list, lambda x: x in {'wolf', 'wolves'})) 
print(count_items(animal_list))