from abc import ABC, abstractmethod

class DataBaseApiInterface(ABC):
    @abstractmethod
    def _create_engine(self):
        pass

    @abstractmethod
    def _create_session(self):
        pass