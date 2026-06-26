# Truco Multiplayer

Truco local multiplayer game para a disciplina de Sistemas Operacionais.

O jogo utiliza o **Gerenciamento de Memória Compartilhada** para manter e sincronizar o estado global da partida (como a mesa e o placar) de forma correta entre os processos. A comunicação ocorre por **Troca de Mensagens** via Sockets, permitindo o envio de comandos (*send* e *recv*). Além disso, o servidor faz o uso de mecanismos de **Exclusão Mútua** para evitar condições de corrida.

| Alunos                         | RA       |
| ----------------------------- | -------- |
| Caio César Jordão Paccagnella | RA 138549 |
| Matheus Henrique Borsato      | RA 138246 |

## Dependências e Pré-requisitos

Para executar este projeto, é necessário que o **Python 3.8 ou superior** esteja instalado na máquina desejada.

O projeto foi desenvolvido utilizando bibliotecas nativas do Python, o que significa que **não é necessário** instalar pacotes externos via `pip`.

**Bibliotecas Nativas Utilizadas:**

- `socket`, `json`, `threading`, `time`, `random`, `dataclasses`, `enum`
- `multiprocessing.shared_memory` _(Requer Python >= 3.8)_
- `tkinter` _(Interface Gráfica)_

**Atenção:** para usuários de Linux: Embora o `tkinter` venha embutido nos instaladores do Windows e macOS, em algumas distribuições Linux pode ser necessário instalá-lo manualmente. Em sistemas baseados em Debian/Ubuntu, utilize:

> ```bash
> sudo apt-get install python3-tk
> ```

## Como Executar o Jogo

Abra o terminal (ou Prompt de Comando) na pasta raiz onde os arquivos do projeto estão localizados e siga os passos abaixo:

### Passo 1: Iniciar o Servidor

O servidor é responsável por manter as regras de negócio, gerenciar os turnos e alocar a memória compartilhada. Em um terminal, execute:

```bash
$ python Servidor.py
```

### Passo 2: Iniciar o Primeiro Jogador (Cliente)

Abra um novo terminal (separado do servidor) na mesma pasta e inicie a interface do primeiro jogador:

```bash
$ python Cliente.py
```

### Passo 3: Iniciar o Segundo Jogador (Cliente)

Abra um terceiro terminal e inicie o segundo cliente para fechar a mesa e iniciar a partida:

```bash
$ python Cliente.py
```
