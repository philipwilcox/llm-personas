class Primitives:

    @staticmethod
    def factorial(x: int) -> int:
        if x < 0:
            raise Exception('cannot get factorial of negative number')
        elif x == 0:
            return 1
        else:
            return x * Primitives.factorial(x - 1)
