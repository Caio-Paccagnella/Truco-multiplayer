import socket
import json
import time
from multiprocessing.shared_memory import SharedMemory

from Partida import Partida
from Carta import Carta

def atualiza_memoria_compartilhada(shared_memory: SharedMemory, partida: Partida):
    cartas_mesa: dict[str, dict[str, str | bool]] = {}
    for id_jogador, (carta, encoberta) in partida.rodada_atual.mesa.jogadas.items():
        if encoberta:
            cartas_mesa[str(id_jogador)] = {
                "carta": "?",
                "encoberta": True    
            }
        else:
            cartas_mesa[str(id_jogador)] = {
                "carta": str(carta),
                "encoberta": False
            }
    
    vira: Carta = partida.rodada_atual.mesa.get_vira()
    estado_compartilhado = {
        "placar": f" Time 1: {partida.placar.time1} X  Time 2: {partida.placar.time2}",
        "vez": partida.rodada_atual.vez,
        "valor_rodada": partida.rodada_atual.valor_apostado,
        "queda_atual": partida.rodada_atual.mesa.get_queda_atual(),
        "vira": str(vira), 
        "mesa": cartas_mesa    
    }
    
    # Converte o dicionário em um JSON
    dados_json: str = json.dumps(estado_compartilhado)
    # Copia o JSON para a memória compartilhada.
    shared_memory.buf[:1024] = dados_json.ljust(1024).encode("utf-8")
    
def main() -> None:
    shared_memory = None
    try:
        shared_memory = SharedMemory("MesaTruco", True, 1024)
    except:
        shared_memory = SharedMemory("MesaTruco", False)
    
    num_jogadores: int = 2
    partida: Partida = Partida(num_jogadores)
    atualiza_memoria_compartilhada(shared_memory, partida)
    server = None
    conexoes = []
    
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Permite reutilizar a porta imediatamente se o script for reiniciado
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        server.bind(("0.0.0.0", 1234))

        server.listen(num_jogadores)
        print("Listening na porta 1234...")


        for i in range(num_jogadores):
            client_socket, address = server.accept()
            conexoes.append(client_socket)
            print(f"Conectado... \nCliente IP: {address[0]}")

            # 1. Servidor toma a iniciativa e envia as instruções
            client_socket.send(f"Bem vindo! Você é o jogador dee ID {i}\n".encode())
            time.sleep(1.0)
        
        print("\n Todos os jogadores conectados!")
        atualiza_memoria_compartilhada(shared_memory, partida)
        
        while not partida.get_finalizada():
            jogador_da_vez: int = partida.rodada_atual.vez
            socket_atual = conexoes[jogador_da_vez]
            
            mao_atual: list[Carta] = partida.jogadores[jogador_da_vez].get_cartas()
            socket_atual.send(f"Cartas:\n\n{mao_atual}\n".encode())
            
            msg: str = socket_atual.recv(1024).decode().strip()
            if not msg:  # Se o cliente desconectar abruptamente
                break

            print(f"Cliente tentou: {msg}")

            if msg == "/sair":
                socket_atual.send(b"Saindo... Tchau!\n")
                break
            elif msg.startswith("JOGAR:"):
                partes: list[str] = msg.split(":")
                indice_carta: int = int(partes[1])
                encoberta: bool = False
                if len(partes) > 2 and partes[2] == "COBERTA":
                    encoberta = True

                partida.recebe_comando_carta(jogador_da_vez, indice_carta, encoberta)
                socket_atual.send(b"JOGADA_OK")
            elif msg == "TRUCO":
                partida.recebe_comando_truco(jogador_da_vez)
                socket_atual.send(b"JOGADA_OK")

            atualiza_memoria_compartilhada(shared_memory, partida)

    except Exception as e:
        print("Erro: ", e)
    finally:
        if server:
            server.close()
        for conexao in conexoes:
            try:
                conexao.close()
            except Exception:
                pass
        shared_memory.close()
        shared_memory.unlink()


if __name__ == "__main__":
    main()
    
    