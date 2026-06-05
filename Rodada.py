from enum import Enum
from Carta import Carta
from Baralho import Baralho
from Mesa import Mesa, Resultado_Queda
from Jogador import Jogador

class EstadoRodada(Enum):
    NORMAL = 0
    AGUARDANDO_RESPOSTA = 1
    
class Rodada:

    estado: EstadoRodada
    jogadores: list[Jogador]
    contador_quedas: list[Resultado_Queda]
    mesa: Mesa
    baralho: Baralho
    pe: int
    vez: int
    id_jogador_inicio: int
    id_jogador_aumentou_valor: int
    valor_apostado: int
    eh_mao_onze: bool
    
    def __init__(self, jogadores: list[Jogador], id_pe_inicial: int, mao_onze: bool):
        self.jogadores = jogadores
        self.pe = id_pe_inicial
        self.vez = (self.pe + 1) % len(self.jogadores)
        self.id_jogador_inicio = self.vez
        self.eh_mao_onze = mao_onze
        self.mesa = Mesa()
        self.baralho = Baralho()
        self.reseta_rodada()
        
    
    def reseta_rodada(self):
        self.valor_apostado = 1
        if self.eh_mao_onze:
            self.valor_apostado = 3
        self.contador_quedas = [Resultado_Queda.NULO] * 3
        self.estado = EstadoRodada.NORMAL
        self.id_jogador_aumentou_valor = -1
        self.baralho.reconstroi()
        self.mesa.reseta_mesa()
        
    def inicia_rodada(self):
        self.baralho.embaralha()
        vira = self.baralho.retira_uma()
        self.mesa.set_vira(vira)
        for jogador in self.jogadores:    
            cartas_jogador = [self.baralho.retira_uma(), self.baralho.retira_uma(), self.baralho.retira_uma()]
            jogador.recebe_cartas(cartas_jogador)
        
    def pode_aumento(self, id_jogador_atual: int) -> bool:
        # Verifica se um jogador pode aumentar o valor apostado.
        if self.eh_mao_onze:
            return False
        if self.valor_apostado == 12:
            return False
        if self.valor_apostado == 1:
            return True
        time_atual = id_jogador_atual % 2
        time_que_aumentou = self.id_jogador_aumentou_valor % 2       
        return time_atual != time_que_aumentou
    
    def sinaliza_pedido_aumento(self, id_autor: int):
        self.estado = EstadoRodada.AGUARDANDO_RESPOSTA
        self.id_jogador_aumentou_valor = id_autor
    
    def verifica_valor_aumento(self) -> int:
        if self.valor_apostado == 12:
            return self.valor_apostado
        valores: dict[int, int] = {1: 3, 3: 6, 6: 9, 9: 12}
        return valores.get(self.valor_apostado)
    
    def aceita_aumento(self):
        self.valor_apostado = self.verifica_valor_aumento()
        self.estado = EstadoRodada.NORMAL
            
    def computa_jogada(self, id_jogador: int, indice_carta: int, encoberta: bool) -> bool:
        
        jogador: Jogador = self.jogadores[id_jogador]
        carta: Carta = jogador.get_cartas() [indice_carta]
        jogador.joga_carta(carta)
        self.mesa.recebe_jogada(id_jogador, carta, encoberta)
        self.vez = (self.vez + 1) % len(self.jogadores)
        
        # Fim da Queda:
        if len(self.mesa.jogadas) == len(self.jogadores):
            resultado_queda: tuple[Resultado_Queda, int] = self.mesa.avalia_vencedor_mesa()
            queda_atual = self.mesa.get_queda_atual()
            self.contador_quedas[queda_atual - 1] = resultado_queda[0]
            
            if resultado_queda[1] != -1:
                self.vez = resultado_queda[1]
            else:
                self.vez = self.id_jogador_inicio
            
            self.id_jogador_inicio = self.vez
            
            if self.mesa.get_queda_atual() < 3:
                self.mesa.set_queda_atual(self.mesa.get_queda_atual() + 1)
                self.mesa.reseta_mesa()
            return True

        # Continua a Queda:
        return False
    
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

