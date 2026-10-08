

animal_list = ['wolf', 'cat', 'wolf pack', 'wolf', 'wolves', 'wolf']
 
wolves = [a for a in animal_list if 'wol' in a]


print(wolves)




counts = {}
for a in animal_list:
    if a in counts:
        counts[a] += 1
    else:
        counts[a] = 1
print(counts)


# wolves = [count(a) for a in animal_list if 'wol' in a]
