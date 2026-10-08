# Filter a list by some condition
def select_by_condition(items, predicate):
    return [item for item in items if predicate(item)]

def select_by_attributes(items, allowed):
    return [item for item in items if item in allowed]

# Wrapping for count
def show(label, items, predicate):
    result = filter_list(items, predicate)
    print(f"{label}: {result} (count={len(result)})")

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

    cars = ["Ford", "Volvo", "BMW"]
    integers = [12, 22, 56, 78, 123, 900]

    print(select_by_condition(cars, lambda car: "F" not in car))

    print(select_by_condition(integers, lambda n: n == 2))
    print(select_by_condition(integers, lambda n: "2" in str(n)))
    print(select_by_condition(integers, lambda n: n % 2 == 0))

    show("Cars without F", cars, lambda car: "F" not in car)
    show("Equals 2", integers, lambda n: n == 2)
    show("Contains 2", integers, lambda n: "2" in str(n))
    show("Even", integers, lambda n: n % 2 == 0)