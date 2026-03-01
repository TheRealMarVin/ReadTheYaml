class BaseDummyType():
    def __init__(self, value:int):
        self.value = value


class DummyTypeA(BaseDummyType):
    def __init__(self, value:int, second:int):
        super().__init__(value)
        self.value = value
        self.second = second


class DummyTypeB(BaseDummyType):
    def __init__(self, value:int, second:str, third:int):
        super().__init__(value)
        self.value = value
        self.second = second
        self.third = third


class UnrelatedDummyType():
    def __init__(self, value:int, second:int):
        super().__init__(value)
        self.value = value
        self.second = second