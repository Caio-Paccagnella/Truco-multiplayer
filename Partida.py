from dataclasses import dataclass
from Jogador import Jogador
from Rodada import Rodada, EstadoRodada
from Mesa import Resultado_Queda


@dataclass
class Placar:
    time1: int
    time2: int
  
class Partida:
    
    placar: Placar
    jogadores: list[Jogador]
    rodada_atual: Rodada
    id_pe: int
    finalizada: bool

    def __init__(self, num_jogadores: int):
        # Controle de quantidade:
        if num_jogadores % 2 != 0 or num_jogadores > 6:
            num_jogadores = 4
            
        self.placar = Placar(0, 0)
        self.jogadores = [Jogador(i) for i in range(num_jogadores)]
        self.id_pe = 0
        self.finalizada = False
        self.nova_rodada()
    
    def get_finalizada(self):
        return self.finalizada
    
    def nova_rodada(self):
        alguem_com_onze = self.placar.time1 == 11 or self.placar.time2 == 11
        self.rodada_atual = Rodada(self.jogadores, self.id_pe, alguem_com_onze)
        self.rodada_atual.inicia_rodada() 
         
    def recebe_comando_carta(self, id_jogador: int, indice_carta: int, encoberta: bool):
        if self.rodada_atual.estado == EstadoRodada.NORMAL and self.rodada_atual.vez == id_jogador:
            fim_queda: bool = self.rodada_atual.computa_jogada(id_jogador, indice_carta, encoberta)
            if fim_queda:
                fim_rodada, vencedor_rodada, pontos = self.rodada_atual.verifica_termino()
                if fim_rodada:
                    self.computa_rodada(vencedor_rodada, pontos)
                    
    def recebe_comando_truco(self, id_jogador: int):
        if self.rodada_atual.estado == EstadoRodada.NORMAL and self.rodada_atual.vez == id_jogador:
            if self.rodada_atual.pode_aumento(id_jogador):
                self.rodada_atual.sinaliza_pedido_aumento(id_jogador)

    def responde_aumento(self, id_jogador: int, aceitou: bool):
        if self.rodada_atual.estado == EstadoRodada.AGUARDANDO_RESPOSTA:
            if (id_jogador % 2) != (self.rodada_atual.id_jogador_aumentou_valor % 2):
                if aceitou:
                    self.rodada_atual.aceita_aumento()
                else:
                    if self.rodada_atual.id_jogador_aumentou_valor % 2 == 0:
                        vencedor = Resultado_Queda.VITORIA_TIME1 
                    else:
                        vencedor = Resultado_Queda.VITORIA_TIME2
                    self.computa_rodada(vencedor, self.rodada_atual.valor_apostado)     
                              
    def get_placar(self):
        return self.placar

    def computa_rodada(self, resultado: Resultado_Queda, pontos: int):
        if resultado == Resultado_Queda.VITORIA_TIME1:
            self.placar.time1 += pontos
        elif resultado == Resultado_Queda.VITORIA_TIME2:
            self.placar.time2 += pontos
            
        self.id_pe = (self.id_pe + 1) % len(self.jogadores)
        
        if self.placar.time1 >= 12 or self.placar.time2 >= 12:
            self.finalizada = True
        else:
            self.nova_rodada()
            
            