def sumOfNumbers(integers):
    numberSum = 0
    for integer in integers:
        if "2" not in str(integer):
            numberSum = numberSum + integer
    return numberSum 

integers = [1,2,3,4]
print(sumOfNumbers(integers)) # 8 