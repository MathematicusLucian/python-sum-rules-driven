class SumClass:

    def sumOfNumbers(integers):
        numberSum = 0
        for integer in integers:
            if "2" not in str(integer):
                numberSum = numberSum + integer
        return numberSum 


sumObj = SumClass

integers = [1,2,3,4]
print(sumObj.sumOfNumbers(integers)) # 8 