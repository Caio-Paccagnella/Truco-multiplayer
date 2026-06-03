from dataclasses import dataclass
from enum import Enum
from Baralho import Carta, Baralho, Naipe
import random

class Resultado_Queda(Enum):
    VITORIA_TIME1 = 1
    VITORIA_TIME2 = 2
    EMPATE = 3
    NULO = 4

@dataclass
class Placar:
    time1: int
    time2: int

class Jogador:
    id_player: int
    cartas: list[Carta]
    
    
    def __init__(self, id):
        self.id_player = id
        self.cartas = []
    
    def recebe_cartas(self, lst: list[Carta]):
        self.cartas = lst

    def joga_carta(self, c: Carta):
        
        self.cartas.remove(c)

    def get_cartas(self):
        return self.cartas


    
class Mesa:
    
    jogadas: dict[int, tuple[Carta, bool]]
    vira: Carta
    queda_atual: int
    
    def set_queda_atual(self, nova_queda: int):
        self.queda_atual = nova_queda
    
    def get_queda_atual(self):
        return self.queda_atual
    
    def __init__(self):
        self.vira = Carta(-1, Naipe.OURO) # Inválido no começo
        self.jogadas = {}
        self.queda_atual = 1
    
    def set_vira(self, vira_rodada: Carta):
        self.vira = vira_rodada
    
    def recebe_jogada(self, id_jogador: int, carta: Carta, encoberta: bool):
        self.jogadas[id_jogador] = (carta, encoberta)
    
    def reseta_mesa(self):
        self.jogadas.clear()
        # self.vira = Carta(-1, Naipe.OURO) # Inválido no começo   
    
    def avalia_vencedor_mesa(self) -> Resultado_Queda:
        aux = self.jogadas.keys()
        verifi: list[tuple[int, Carta]] = []
        for n in aux: #faço isso aqui e nao na chave direto para validar o inteiro certo caso nao venha o padrao
            #pega as cartas validas (nao viradas)
            c, encoberta = self.jogadas[n]
            if not encoberta:
                verifi.append((n, c))
        
        # aq funciona so para 2 players:
        if len(verifi) == 2:
            id_jog1, carta1 = verifi[0]
            id_jog2, carta2 = verifi[1]
            carta_maior = compara_carta(carta1, carta2, self.vira)
            
            # Se a função retornar None, ocorreu um empate (cartas de mesma força)
            if carta_maior is None:
                return Resultado_Queda.EMPATE
                
            id_vencedor = id_jog1 if carta_maior == carta1 else id_jog2
            return Resultado_Queda.VITORIA_TIME1 if id_vencedor == 0 else Resultado_Queda.VITORIA_TIME2
        elif len(verifi) == 1:
            #aqui o id tem que ser 0 do jogador 1
            return Resultado_Queda.VITORIA_TIME1 if verifi[0][0] == 0 else Resultado_Queda.VITORIA_TIME2
        else: #elif verifi == []:
            return Resultado_Queda.EMPATE


def compara_carta(carta1: Carta, carta2: Carta, vira: Carta) -> Carta | None:
    
    ordem_forca: list[int] = [4, 5, 6, 7, 8, 9, 10, 1, 2, 3]
    indice_vira = ordem_forca.index(vira.valor)
    indice_manilha = (indice_vira + 1) % len(ordem_forca)
    valor_manilha = ordem_forca[indice_manilha]
    
    if carta1.valor == valor_manilha and carta2.valor != valor_manilha:
        return carta1
    elif carta2.valor == valor_manilha and carta1.valor != valor_manilha:
        return carta2
    elif carta1.valor == valor_manilha and carta2.valor == valor_manilha:
        return carta1 if carta1.naipe.value > carta2.naipe.value else carta2
    else:
        indice_forca1: int = ordem_forca.index(carta1.valor)
        indice_forca2: int = ordem_forca.index(carta2.valor)       
        if indice_forca1 > indice_forca2:
            return carta1
        elif indice_forca2 > indice_forca1:
            return carta2
    return None
        
    
class Rodada:

    pe: int
    vez: int
    mesa: Mesa
    valor_apostado: int
    contador_quedas: list[Resultado_Queda] # registra cada vencedor de cada queda sendo 1 para o time 1 e 2 para o time 2
    baralho: Baralho
    jogadores: list[Jogador] # <- referência aos jogadores
    
    def __init__(self, jogadores: list[Jogador]):
        
        self.pe = random.randint(0, 1)
        self.vez = 1 - self.pe
        self.mesa = Mesa()
        self.valor_apostado = 1
        self.contador_quedas = [Resultado_Queda.NULO] * 3
        self.baralho = Baralho()
        self.jogadores = jogadores
        
    
    def reseta_rodada(self):
        self.valor_apostado = 1
        self.contador_quedas = [Resultado_Queda.NULO] * 3
        self.baralho.reconstroi()
        
    def inicia_rodada(self):
        self.baralho.embaralha()
        vira = self.baralho.retira_uma()
        self.mesa.set_vira(vira)
        for jogador in self.jogadores:
           
            mao = [self.baralho.retira_uma(), self.baralho.retira_uma(), self.baralho.retira_uma()]
            jogador.recebe_cartas(mao)
        
        

    def finaliza_queda(self):
        vencedor_queda: Resultado_Queda = self.mesa.avalia_vencedor_mesa()
        queda_atual: int = self.mesa.get_queda_atual()
        self.contador_quedas[queda_atual - 1] = vencedor_queda
        if not self.verifica_termino()[0]:
            self.mesa.set_queda_atual(queda_atual + 1)
        else:
            self.mesa.set_queda_atual(1)
    
    def verifica_termino(self) -> tuple[bool, Resultado_Queda, int]:
        r1 = self.contador_quedas[0]
        r2 = self.contador_quedas[1]
        r3 = self.contador_quedas[2]

        if r1 == Resultado_Queda.EMPATE:
            if r2 == Resultado_Queda.EMPATE:
                # Três empates: a mão morre e ninguém pontua
                if r3 == Resultado_Queda.EMPATE:
                    return True, Resultado_Queda.NULO, 0 
                
                elif r3 != Resultado_Queda.NULO:
                    return True, r3, self.valor_apostado
            
            # Quem ganha a segunda rodada leva a mão direto
            elif r2 != Resultado_Queda.NULO:
                return True, r2, self.valor_apostado

        elif r1 != Resultado_Queda.NULO and r1 != Resultado_Queda.EMPATE:
            # Ganhou primeira e segunda seguidas
            if r2 == r1:
                return True, r1, self.valor_apostado
            
            # Ganhou a primeira e a segunda empatou: o da primeira leva
            elif r2 == Resultado_Queda.EMPATE:
                return True, r1, self.valor_apostado
            
            # Teve terceira rodada (cada time ganhou uma)
            elif r2 != Resultado_Queda.NULO: 
                # Empate na terceira: o vencedor da primeira (r1) leva
                if r3 == Resultado_Queda.EMPATE:
                    return True, r1, self.valor_apostado
                
                elif r3 != Resultado_Queda.NULO:
                    return True, r3, self.valor_apostado

        return False, Resultado_Queda.NULO, 0


    def termina_rodada(self, pe: int):
        self.pe = pe
        self.vez = 1 - self.pe
        self.reseta_rodada()
        
    
class Partida:
    
    placar: Placar
    jogadores: list[Jogador]
    rodada_atual: Rodada

    def __init__(self, num_jogadores: int = 2):
        self.placar = Placar(0, 0)
        # Cria os jogadores com IDs de 0 até num_jogadores-1
        self.jogadores = [Jogador(i) for i in range(num_jogadores)]
        
        # Inicia a primeira rodada passando os jogadores
        self.rodada_atual = Rodada(self.jogadores)
    
    def atualiza_placar(self, valor_rodada: int, vencedor: int):
        if vencedor == 1:
            self.placar.time1 += valor_rodada
        else:
            self.placar.time2 += valor_rodada

    def get_placar(self):
        return self.placar