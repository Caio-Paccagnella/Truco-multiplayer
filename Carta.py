from __future__ import annotations
from enum import Enum
from dataclasses import dataclass

class Naipe(Enum):
    OURO = 0
    ESPADA = 1
    COPAS = 2
    PAUS = 3

@dataclass
class Carta:
    valor: int
    naipe: Naipe
    
    def compara_cartas(self, outra: Carta, vira: Carta) -> Carta | None:
        
        # Lógica considerando o Truco Paulista tradicional, sem manilha fixa:
        ordem_forca: list[int] = [4, 5, 6, 7, 8, 9, 10, 1, 2, 3]
        indice_vira = ordem_forca.index(vira.valor)
        indice_manilha = (indice_vira + 1) % len(ordem_forca)
        valor_manilha = ordem_forca[indice_manilha]
        
        if self.valor == valor_manilha and outra.valor != valor_manilha:
            return self
        elif outra.valor == valor_manilha and self.valor != valor_manilha:
            return outra
        elif self.valor == valor_manilha and outra.valor == valor_manilha:
            if self.naipe.value >= outra.naipe.value:
                return self
            else:
                return outra
        else:
            indice_forca1: int = ordem_forca.index(self.valor)
            indice_forca2: int = ordem_forca.index(outra.valor)       
            if indice_forca1 > indice_forca2:
                return self
            elif indice_forca2 > indice_forca1:
                return outra
        return None
    
    