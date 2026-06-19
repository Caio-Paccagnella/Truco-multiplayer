from enum import Enum
from Carta import Carta, Naipe

class Resultado_Queda(Enum):
    VITORIA_TIME1 = 1
    VITORIA_TIME2 = 2
    EMPATE = 3
    NULO = 4
    
class Mesa:
    
    jogadas: dict[int, tuple[Carta, bool]]
    vira: Carta
    queda_atual: int
 
    def __init__(self):
        self.vira = Carta(-1, Naipe.OURO) # Inválido no começo
        self.jogadas = {}
        self.queda_atual = 1   
        
    def set_queda_atual(self, nova_queda: int):
        self.queda_atual = nova_queda
    
    def get_queda_atual(self):
        return self.queda_atual
       
    def set_vira(self, vira_rodada: Carta):
        self.vira = vira_rodada
    
    def get_vira(self) -> Carta:
        return self.vira
    
    def recebe_jogada(self, id_jogador: int, carta: Carta, encoberta: bool):
        self.jogadas[id_jogador] = (carta, encoberta)
    
    def reseta_mesa(self):
        # Limpa o Dicionário que armazena as jogadas.
        self.jogadas.clear() 
    
    def avalia_vencedor_mesa(self) -> tuple[Resultado_Queda, int]:
        # Retorna o resultado e o id do jogador com a maior carta,
        # considerando mais de 2 jogadores.
        aux = self.jogadas.keys()
        validas: list[tuple[int, Carta]] = []
        
        # Remove as cartas que foram encobertas.
        for n in aux:
            c, encoberta = self.jogadas[n]
            if not encoberta:
                validas.append((n, c))
        
        if not validas:
            return Resultado_Queda.EMPATE, -1
        
        # Pega a maior (ou as maiores) cartas da mesa.
        maior_carta: list[tuple[int, Carta]] = [validas[0]]
        for id_jogador, carta in validas[1:]:
            _, carta_atual_maior = maior_carta[0]
            
            resultado_comparacao = carta.compara_cartas(carta_atual_maior, self.vira)
            if resultado_comparacao == carta:
                maior_carta = [(id_jogador, carta)]
            elif resultado_comparacao is None:
                maior_carta.append((id_jogador, carta))
            else: # A carta que está em "maior_carta" já é a maior.
                pass
        
        # Verifica qual time ganhou a queda, com base nas maiores cartas
        # associadas a quem as jogou.
        maior_carta_time1: bool = False
        maior_carta_time2: bool = False
        
        id_vencedor: int = maior_carta[0][0]
        
        for id_jogador, carta in maior_carta:
            if id_jogador % 2 == 0:
                maior_carta_time1 = True
            else:
                maior_carta_time2 = True
                
        if maior_carta_time1 and maior_carta_time2:
            return Resultado_Queda.EMPATE, -1
        if maior_carta_time1:
            return Resultado_Queda.VITORIA_TIME1, id_vencedor
        else:
            return Resultado_Queda.VITORIA_TIME2, id_vencedor



