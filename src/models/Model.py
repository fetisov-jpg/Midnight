from abc import ABC, abstractmethod


class Model(ABC):
    def __init__(self, name, surname, login, password):
        self._name = name
        self._surname = surname
        self._login = login
        self._password = password

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def surname(self) -> str:
        return self._surname

    @surname.setter
    def surname(self, value: str) -> None:
        self._surname = value

    @property
    def login(self) -> str:
        return self._login

    @login.setter
    def login(self, value: str) -> None:
        self._login = value

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        self._password = value

    @abstractmethod
    def to_dict(self):
        return {
            "name": self.name,
            "surname": self.surname,
            "login": self.login,
            "password": self.password,
        }
