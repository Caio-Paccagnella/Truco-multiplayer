import socket
import json
import time
from multiprocessing.shared_memory import SharedMemory

def ler_memoria_compartilhada(shared_memory: SharedMemory):
    dados_brutos = bytes(shared_memory.buf[:1024]).decode("utf-8").strip()
    return json.loads(dados_brutos)

def print_mesa_truco(estado: dict):
    print("\n" + "-" * 50)
    print(f" {estado['placar']}")
    print(f" Queda: {estado['queda_atual']}ª")
    print(f" Valor apostada na rodada: {estado['valor_rodada']} pontos")
    print("-" * 50)
    print(f" O vira é: [ {estado['vira']} ]")
    print("-" * 50)
    print(" Cartas jogadas na mesa:")
    
    mesa_atual = estado["mesa"]
    if not mesa_atual:
        print(" \nMesa vazia, ninguém jogou nesta rodada ainda!")
    else:
        for id_jogador, dados_carta in mesa_atual.items():
            print(f" -> Jogador {id_jogador} jogou: [ {dados_carta['carta']} ]")
    print("-" * 50)

def main():
    client = None
    shared_memory = None
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)

        # IP do servidor
        client.connect(("127.0.0.1", 1234)) #host local

        # Recebe a mensagem de boas-vindas do servidor
        boas_vindas = client.recv(1024).decode("utf-8")
        print("Servidor:", boas_vindas)
        meu_id: int = int(boas_vindas.strip().split()[-1])
        shared_memory = SharedMemory("MesaTruco", False)
        ultima_vez: int = -1
        while True:
            estado = ler_memoria_compartilhada(shared_memory)
            
            if estado["vez"] != ultima_vez:
                ultima_vez = estado["vez"]
                print_mesa_truco(estado)
            
            if estado["vez"] == meu_id:
                print(" \nSua vez de jogar +++++++++++++\n ")
                
                dados = client.recv(1024).decode()
                print(dados)
                print(" COMANDOS VÁLIDOS:")
                print(" JOGAR:0         (Joga a 1ª carta aberta)")
                print(" JOGAR:1:COBERTA (Joga a 2ª carta escondida)")
                print(" TRUCO           (Pede truco / aceita)")
                print(" /sair           (Abandona o jogo)")
                
                comando = input("\nDigite sua ação: ")

                if not comando:
                    ultima_vez = -1
                    continue

                # Envia para o servidor
                client.send(comando.encode())

                if comando == "/sair":
                    break
                
                confirmacao = client.recv(1024).decode()
                time.sleep(1.0)
            else:
                print(f"Aguardando a jogada do Jogador {estado['vez']}", end="\r")
                time.sleep(1.0)

    except Exception as e:
        print("Erro de conexão:", e)
    finally:
        client.close()
        shared_memory.close()


if __name__ == "__main__":
    main()