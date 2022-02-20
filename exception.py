class URLNotValid(Exception):
    """Исключение в случае недоступности URL"""
    def __init__(self, value):
        self.message = f'Эндпойнт {value} неверный.'
        super().__init__(self.message)
    
    def __str__(self):
        return self.message


class URLNotResponding(Exception):
    """Исключение в случае недоступности URL"""
    def __init__(self, value):
        self.message = f'URL {value} не отвечает.'
        super().__init__(self.message)
    
    def __str__(self):
        return self.message


class UnknownStatus(Exception):
    """Исключение в случае недокументированного статуса"""
    def __init__(self, value):
        self.message = f'Статус {value} отсутствует в словаре.'
        super().__init__(self.message)
    
    def __str__(self):
        return self.message


class InvalidJsonKey(Exception):
    """Исключение в случае отсутсвия ключа"""
    def __init__(self, value):
        self.message = f'По ключу {value} нет данных.'
        super().__init__(self.message)
    
    def __str__(self):
        return self.message
