def select_by_condition(items, predicate):
    return [item for item in items if predicate(item)]

def select_by_attributes(items, allowed):
    return [item for item in items if item in allowed]

def count_items(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


animal_list = ['wolf', 'cat', 'wolf pack', 'wolf', 'wolves', 'wolf'] 

print(select_by_condition(animal_list, lambda x: 'wol' in x))
print(select_by_condition(animal_list, lambda x: x in {'wolf', 'wolves'})) 
print(select_by_attributes(animal_list, {'wolf'}))
print(select_by_attributes(animal_list, {'wolf', 'wolves'}))
print(count_items(animal_list))