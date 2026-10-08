from functools import partial


# ---------------------------------------------------------------------------
# SumClass — every method
# ---------------------------------------------------------------------------

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

    sumOfNumbers6 = lambda integers, condition: sum(
        integer for integer in integers if condition(integer)
    )


# ---------------------------------------------------------------------------
# Runtime data
# ---------------------------------------------------------------------------
sumObj = SumClass

integers = [1,2,3,4]

# --- named condition callables (kept as plain typed variables) ------------
sumExcludingTwo = lambda integer: integer != 2
sumExcludingTwoB = lambda integer: "2" not in str(integer)

# factory returning a Condition
sumExcludingFactory = lambda integerToExclude: (lambda integer: integer != integerToExclude)

# two-arg predicates (candidates for partial)
sumExcludingPredicate = lambda integer, integerToExclude: integer != integerToExclude
sumIncludingPredicate = lambda integer, integerToExclude: integer == integerToExclude

onlyEvens = lambda integer: integer % 2 == 0
onlyOdds = lambda integer: integer % 2 == 1

# partial pre-binds the keyword integerToExclude=2 (condition param name otherwise binds 2 to `integer`)
sumExcludingPredicateWithCondition = partial(sumExcludingPredicate, integerToExclude=2) #8
sumIncludingPredicateWithCondition = partial(sumIncludingPredicate, integerToExclude=2) #8 


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------
print(sumObj.sumOfNumbers1(integers))                                        # 8
print(sumObj.sumOfNumbers1b(integers, sumExcludingTwo))                      # 8
print(sumObj.sumOfNumbers2(integers))                                        # 8
print(sumObj.sumOfNumbers2b(integers, sumExcludingTwo))                      # 8
print(sumObj.sumOfNumbers3(integers))                                        # 8
print(sumObj.sumOfNumbers4(integers))                                        # 8
print(sumObj.sumOfNumbers5(integers))                                        # 8
print(sumObj.sumOfNumbers6(integers, sumExcludingTwo))                       # 8
print(sumObj.sumOfNumbers6(integers, sumExcludingTwoB))                      # 8
print(sumObj.sumOfNumbers6(integers, sumExcludingFactory(2)))                # 8
print(sumObj.sumOfNumbers6(integers, sumExcludingPredicateWithCondition))    # 8

print(sumObj.sumOfNumbers6(integers, sumIncludingPredicateWithCondition))    # 2

print(sumObj.sumOfNumbers6(integers, onlyEvens))                             # 6
print(sumObj.sumOfNumbers6(integers, onlyOdds))                              # 4