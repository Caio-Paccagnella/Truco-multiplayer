from enum import Enum
from dataclasses import dataclass
from Carta import Carta


class Acao(Enum):
    JOGAR = 0
    ENCOBRIR = 1
    AUMENTAR_VALOR = 3
    ACEITAR = 4
    CORRER = 5
    
    
@dataclass
class ComandoJogador:
    tipo: Acao
    carta: Carta | None
    

class Jogador:
    # Representa um jogador com um ID e uma mão de cartas.
    id_player: int
    cartas: list[Carta]
      
    def __init__(self, id: int) -> None:
        self.id_player = id
        self.cartas = []
    
    def get_id(self) -> int:
        return self.id_player
    
    def recebe_cartas(self, lst: list[Carta]) -> None:
        self.cartas = lst[:]

    def joga_carta(self, c: Carta) -> None:
        if c in self.cartas:        
            self.cartas.remove(c)

    def get_cartas(self) -> list[Carta]:
        return self.cartas[:]
    
        
            