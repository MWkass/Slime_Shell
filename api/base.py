from abc import ABC, abstractmethod
from typing import List, Dict, Any

class AnimeProvider(ABC):
    @abstractmethod
    def buscar_anime(self, nome_anime: str) -> List[Dict[str, Any]]:
        """
        Busca um anime pelo nome.
        Retorna uma lista de dicionários com 'titulo_exibicao' e 'url'.
        """
        pass

    @abstractmethod
    def obter_episodios(self, url_anime: str) -> List[Dict[str, Any]]:
        """
        Obtém a lista de episódios de um anime específico.
        Retorna uma lista de dicionários com 'numero' e 'url'.
        """
        pass

    @abstractmethod
    def extrair_links(self, url_episodio: str) -> Dict[str, str]:
        """
        Extrai links de vídeo, retornando um dicionário {'Servidor': 'URL'}.
        """
        pass