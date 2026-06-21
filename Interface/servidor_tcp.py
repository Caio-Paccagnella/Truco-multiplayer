import socket
import json
import time
from multiprocessing.shared_memory import SharedMemory

from Partida import Partida
from Carta import Carta
from Rodada import EstadoRodada


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
        "mesa": cartas_mesa,
        "estado_rodada": partida.rodada_atual.estado.name
    }

    dados_json: str = json.dumps(estado_compartilhado)
    shared_memory.buf[:1024] = dados_json.encode("utf-8").ljust(1024, b" ")


def enviar_cartas_para_todos(conexoes, partida):
    """Envia as cartas de cada jogador para o respectivo socket."""
    for i, jogador in enumerate(partida.jogadores):
        mao = jogador.get_cartas()
        msg = f"Cartas:\n\n{mao}\n"
        try:
            conexoes[i].send(msg.encode())
            print(f"📤 Cartas enviadas para jogador {i}: {mao}")
        except Exception as e:
            print(f"Erro ao enviar cartas para jogador {i}: {e}")


def verifica_e_envia_novas_cartas(conexoes, partida):
    """
    Envia novas cartas apenas se for o início de uma rodada:
    mesa vazia E queda atual == 1.
    """
    if (not partida.rodada_atual.mesa.jogadas and 
        partida.rodada_atual.mesa.get_queda_atual() == 1):
        print("🔄 Nova rodada detectada - enviando cartas.")
        enviar_cartas_para_todos(conexoes, partida)
        return True
    return False


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
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 5555))
        server.listen(num_jogadores)
        print("Servidor ouvindo na porta 5555...")

        for i in range(num_jogadores):
            client_socket, address = server.accept()
            conexoes.append(client_socket)
            print(f"Conectado cliente {i} de {address}")
            client_socket.send(f"Bem vindo! Você é o jogador de ID {i}\n".encode())
            time.sleep(1.0)

        print("Todos os jogadores conectados!")

        # Envia as cartas iniciais
        verifica_e_envia_novas_cartas(conexoes, partida)
        atualiza_memoria_compartilhada(shared_memory, partida)

        while not partida.get_finalizada():
            # Verifica se é uma nova rodada e envia cartas (caso não tenha sido feito)
            verifica_e_envia_novas_cartas(conexoes, partida)
            atualiza_memoria_compartilhada(shared_memory, partida)

            if partida.rodada_atual.estado == EstadoRodada.NORMAL:
                jogador_da_vez = partida.rodada_atual.vez
                socket_atual = conexoes[jogador_da_vez]

                socket_atual.settimeout(60)
                try:
                    msg = socket_atual.recv(1024).decode().strip()
                except socket.timeout:
                    print(f"Timeout do jogador {jogador_da_vez}")
                    break
                except Exception as e:
                    print(f"Erro ao receber do jogador {jogador_da_vez}: {e}")
                    break

                if not msg:
                    break
                print(f"Cliente {jogador_da_vez} enviou: {msg}")

                if msg == "/sair":
                    socket_atual.send(b"Saindo...\n")
                    break
                elif msg.startswith("JOGAR:"):
                    partes = msg.split(":")
                    try:
                        indice_carta = int(partes[1])
                    except (IndexError, ValueError):
                        socket_atual.send(b"COMANDO_INVALIDO")
                        continue

                    encoberta = False
                    if len(partes) > 2 and partes[2] == "COBERTA":
                        encoberta = True

                    # Valida o índice
                    mao = partida.jogadores[jogador_da_vez].get_cartas()
                    if indice_carta < 0 or indice_carta >= len(mao):
                        socket_atual.send(b"COMANDO_INVALIDO")
                        continue

                    # Processa a jogada
                    partida.recebe_comando_carta(jogador_da_vez, indice_carta, encoberta)
                    atualiza_memoria_compartilhada(shared_memory, partida)
                    socket_atual.send(b"JOGADA_OK")

                    # Se a partida acabou, sai do loop
                    if partida.get_finalizada():
                        break

                    # Imediatamente verifica se a rodada terminou e envia novas cartas
                    verifica_e_envia_novas_cartas(conexoes, partida)

                elif msg == "TRUCO":
                    partida.recebe_comando_truco(jogador_da_vez)
                    atualiza_memoria_compartilhada(shared_memory, partida)
                    socket_atual.send(b"JOGADA_OK")

                    if partida.rodada_atual.estado == EstadoRodada.AGUARDANDO_RESPOSTA:
                        adversario = 1 - jogador_da_vez
                        socket_adversario = conexoes[adversario]
                        valor_atual = partida.rodada_atual.valor_apostado
                        socket_adversario.send(f"TRUCO_PEDIDO:{valor_atual}".encode())
                        socket_adversario.settimeout(30)
                        try:
                            resposta = socket_adversario.recv(1024).decode().strip()
                        except socket.timeout:
                            resposta = "CORRER"
                        except Exception as e:
                            print(f"Erro ao receber resposta do adversário: {e}")
                            resposta = "CORRER"

                        print(f"Adversário {adversario} respondeu: {resposta}")
                        if resposta == "ACEITAR":
                            partida.responde_aumento(adversario, True)
                        else:
                            partida.responde_aumento(adversario, False)

                        atualiza_memoria_compartilhada(shared_memory, partida)
                        verifica_e_envia_novas_cartas(conexoes, partida)
                    else:
                        atualiza_memoria_compartilhada(shared_memory, partida)
                        verifica_e_envia_novas_cartas(conexoes, partida)
                else:
                    socket_atual.send(b"COMANDO_INVALIDO")

            elif partida.rodada_atual.estado == EstadoRodada.AGUARDANDO_RESPOSTA:
                time.sleep(0.1)
            else:
                time.sleep(0.1)

            time.sleep(0.05)

        # Fim da partida
        vencedor = "Time 1" if partida.placar.time1 > partida.placar.time2 else "Time 2"
        for sock in conexoes:
            try:
                sock.send(f"FIM_DE_JOGO: Vencedor: {vencedor}".encode())
                sock.close()
            except Exception:
                pass

    except Exception as e:
        print("Erro no servidor:", e)
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