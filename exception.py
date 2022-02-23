class URLNotResponding(Exception):
    """Исключение в случае недоступности URL"""
    def __init__(self, value):
        self.message = f'URL {value} не отвечает.'
        super().__init__(self.message)
    
    def __str__(self):
        return self.message

class EmptyData(Exception):
    """Исключение в случае недоступности URL"""
    def __init__(self, value):
        self.message = f'Нет данных в ответе - {value}'
        super().__init__(self.message)
    
    def __str__(self):
        return self.message
