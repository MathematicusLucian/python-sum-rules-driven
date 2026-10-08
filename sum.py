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
    
    def sumOfNumbers2(integers):
        return [sum(integer for integer in integers if "2" not in str(integer))][0] 
    
    def sumOfNumbers2b(integers, condition):
        return sum(integer for integer in integers if condition(integer))

    def sumOfNumbers3(integers):
        return [sum(integer for integer in integers if integer != 2)][0] 
    
    def sumOfNumbers4(integers):
        return sum(integer for integer in integers if integer != 2) 

    sumOfNumbers5 = lambda integers: sum(integer for integer in integers if integer != 2) 


sumObj = SumClass

integers = [1,2,3,4]

sumExcludingTwo = lambda integer: integer != 2
sumExcludingTwoB = lambda integer: "2" not in str(integer)
sumExcluding = lambda integerToExclude: (lambda integer: integer != integerToExclude)
sumExcludingFactory = lambda integer, integerToExclude: integer != integerToExclude
sumIncludingFactory = lambda integer, integerToExclude: integer == integerToExclude
onlyEvens = lambda integer: integer % 2 == 0
onlyOdds = lambda integer: integer % 2 == 1

print(sumObj.sumOfNumbers1(integers)) # 8
print(sumObj.sumOfNumbers1b(integers, sumExcludingTwo)) # 8
print(sumObj.sumOfNumbers2(integers)) # 8
print(sumObj.sumOfNumbers2b(integers, sumExcludingTwo)) # 8
print(sumObj.sumOfNumbers3(integers)) # 8
print(sumObj.sumOfNumbers4(integers)) # 8
print(sumObj.sumOfNumbers5(integers)) # 8