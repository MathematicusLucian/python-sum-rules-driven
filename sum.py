class SumClass:

    def sumOfNumbers1(integers):
        numberSum = 0
        for integer in integers:
            if "2" not in str(integer):
                numberSum = numberSum + integer
        return numberSum

    def sumOfNumbers1b(integers, condition):
        numberSum = 0
        for integer in integers:
            if condition(integer):
                numberSum = numberSum + integer
        return numberSum 

sumObj = SumClass

integers = [1,2,3,4]

sumExcludingTwo = lambda integer: integer != 2 

print(sumObj.sumOfNumbers1(integers)) # 8
print(sumObj.sumOfNumbers1b(integers, sumExcludingTwo)) # 8 