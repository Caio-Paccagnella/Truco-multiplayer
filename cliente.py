import socket


def main():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(10)

        # IP do servidor
        client.connect(("127.0.0.1", 1234)) #host local

        # Recebe a mensagem de boas-vindas do servidor
        boas_vindas = client.recv(1024).decode("utf-8")
        print("Servidor:", boas_vindas)

        while True:
            # Digita o palpite
            palpite = input("Digite a senha (ou /sair): ")

            if not palpite:
                continue

            # Envia para o servidor
            client.send(palpite.encode("utf-8"))

            # Recebe a resposta do servidor
            resposta = client.recv(1024).decode("utf-8")
            print("Servidor respondeu:", resposta)

            if palpite == "/sair" or "Parabens" in resposta:
                break

        client.close()

    except Exception as e:
        print("Erro de conexão:", e)


if __name__ == "__main__":
    main()