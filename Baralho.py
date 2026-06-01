#Esta biblioteca representa a implementação de um tipo abstrato baralho
from dataclasses import dataclass
from enum import Enum
import random

class Naipe(Enum):
    OURO = 0
    ESPADA = 1
    COPAS = 2
    PAUS = 3

@dataclass
class Carta:
    valor: int
    naipe: Naipe

class Baralho:
    '''
    Representa um baralho de cartas, cujo os valores vão de um à dez e 
    cada valor possui uma carta de cada Naipe
    '''
    cartas: list[Carta]

    def __init__(self):
        self.cartas = []
        for i in range(1, 11):
            self.cartas.append(Carta(i, Naipe.OURO))
            self.cartas.append(Carta(i, Naipe.COPAS))
            self.cartas.append(Carta(i, Naipe.ESPADA))
            self.cartas.append(Carta(i, Naipe.PAUS))

    def embaralha(self) -> None:
        '''
        Embaralha as cartas baseada no método Fisher-Yates
        '''
        random.shuffle(self.cartas)

    def retira_uma(self) -> Carta:
        '''
        Retira uma carta aleatória do baralho

        OBS: mesmo que idealmente o usuário embaralhe antes, esse
        método aumenta a aleatoridade
        '''
        if len(self.cartas) < 0:
            return Carta(-1, Naipe.OURO) # Carta inválida para evitar erros
        index = random.randint(0, len(self.cartas) -1)
        
        carta = self.cartas[index]
        self.cartas[index], self.cartas[-1] = self.cartas[-1], self.cartas[index]
        self.cartas.pop()
        return carta

    def reconstroi(self):
        '''
        Reconstitui o baralho, retornando as cartas retiradas
        (Ele volta com a ordem inicial)
        '''
    
        self.__init__()

# Compartilhado (no servidor) -> 
# Partida -> Placar / Rodada_Atual
# Rodada_Atual -> vez: int, pé: int / Mesa / Valor (1, 3, 6, 9, 12) / Contador_Quedas: 
# Mesa -> list[Cartas], vira: Carta
# Vez -> inteiro com id do jogador
# Jogador -> list[Carta], método de mudar valor da rodada, método de jogar carta (booleano no parâmetro se encobre ou nao)
