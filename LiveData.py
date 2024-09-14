class LiveData:
    def __init__(self):
        self._value = None
        self._observers = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        for callback in self._observers:
            callback(new_value)

    def observe(self, callback):
        self._observers.append(callback)
