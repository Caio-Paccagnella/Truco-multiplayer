from Testes.Partida import Partida, Resultado_Queda

def main():
    partida = Partida(num_jogadores=2)

    jogador1 = partida.jogadores[0] # da para associar cada jogador com um cliente
    jogador2 = partida.jogadores[1]
    rodada = partida.rodada_atual

    while partida.placar.time1 < 12 and partida.placar.time2 < 12:
        # ficar jogando até acabar a partida
        rodada.inicia_rodada()
        
        

        terminou = False
        vencedor_rodada = Resultado_Queda.NULO
        valor_pontos = 0
        vez = partida.rodada_atual.vez
        count = 0
        while not terminou:
            
            print(f"VIRA: {rodada.mesa.vira}")
            print(f"Jogador 1 (Time 1) recebeu: {[f'{c.valor} de {c.naipe.name}' for c in jogador1.get_cartas()]}")
            print(f"Jogador 2 (Time 2) recebeu: {[f'{c.valor} de {c.naipe.name}' for c in jogador2.get_cartas()]}")
            
            if vez == 0:
                # jogador 1
                print("Escolha a carta que vai jogar (posição)")
                i = int(input())
                print("Encobrir(s/n)")
                a = input()
                if a == 's':
                    enc = True
                else: enc = False
                carta = jogador1.get_cartas()[i]
                jogador1.joga_carta(carta)
                rodada.mesa.recebe_jogada(0, carta, enc) 
                vez = 1 - vez
                count += 1

            elif vez == 1:
                #jogador 2
                print("Escolha a carta que vai jogar (posição)")
                i = int(input())
                print("Encobrir(s/n)")
                a = input()
                if a == 's':
                    enc = True
                else: enc = False
                carta = jogador2.get_cartas()[i]
                jogador2.joga_carta(carta)
                rodada.mesa.recebe_jogada(1, carta, enc)
                vez = 1 - vez
                count += 1

            if count == 2:
                # Processa o resultado da queda atual
                count = 0
                vencedor_queda = rodada.mesa.avalia_vencedor_mesa()
                if vencedor_queda == Resultado_Queda.VITORIA_TIME1:
                    vez = 0
                elif vencedor_queda == Resultado_Queda.VITORIA_TIME2:
                    vez = 1
                rodada.finaliza_queda()

                rodada.mesa.reseta_mesa()
                terminou, vencedor_rodada, valor_pontos = rodada.verifica_termino()
            
        if vencedor_rodada == Resultado_Queda.VITORIA_TIME1:
            print(f"FIM DA RODADA TIME 1 venceu")
            partida.atualiza_placar(valor_rodada=valor_pontos, vencedor=1)
        elif vencedor_rodada == Resultado_Queda.VITORIA_TIME2:
            print(f"FIM DA RODADA TIME 2 venceu")
            partida.atualiza_placar(valor_rodada=valor_pontos, vencedor=2)
        else:
            print(f"FIM DA RODADA empatou.")

main()