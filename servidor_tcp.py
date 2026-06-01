import socket


def main():
    server = None
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Permite reutilizar a porta imediatamente se o script for reiniciado
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        server.bind(("0.0.0.0", 1234))

        server.listen(2)
        print("Listening na porta 1234...")

        client_socket, address = server.accept()
        print(f"Conectado... \nCliente IP: {address[0]}")

        # 1. Servidor toma a iniciativa e envia as instruções
        client_socket.send(b"Adivinhe a senha para solicitar o acesso\n")

        while True:
            msg = client_socket.recv(1024).decode().strip()
            if not msg:  # Se o cliente desconectar abruptamente
                break

            print(f"Cliente tentou: {msg}")

            if msg == "/sair":
                client_socket.send(b"Saindo... Tchau!\n")
                break
            elif msg == "supersenha":
                client_socket.send(
                    b"Parabens! Acertou a super senha secreta!! Acesso liberado.\n"
                )
            else:
                client_socket.send(b"Senha incorreta! Tente novamente.\n")

        # Fecha a conexão com ESSE cliente
        client_socket.close()

    except Exception as e:
        print("Erro: ", e)
    finally:
        if server:
            server.close()


if __name__ == "__main__":
    main()