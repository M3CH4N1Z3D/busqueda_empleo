from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def buscar_ofertas(self, cargo):
        """
        Busca ofertas de trabajo para un cargo específico.
        Debe retornar una lista de diccionarios con la información de las ofertas.
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
