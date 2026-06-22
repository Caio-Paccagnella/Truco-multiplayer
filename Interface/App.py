"""
Este arquivo representa o cliente, que se conecta ao servidor para jogar o truco.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import time
import threading
from multiprocessing.shared_memory import SharedMemory

# Paleta de cores:
BG_FELT       = "#1B4D35"
BG_DARK       = "#122E20"
BG_CARD       = "#FAF6EE"
BG_CARD_BACK  = "#1A2E6B"
ACCENT_GOLD   = "#C9A84C"
ACCENT_RED    = "#C0392B"
TEXT_LIGHT    = "#F0EBE0"
TEXT_DARK     = "#1A1008"
TEXT_MUTED    = "#8FA898"
BTN_GREEN     = "#27AE60"
BTN_RED_BG    = "#922B21"
BTN_TRUCO     = "#A04000"
BTN_HOVER     = "#F0C040"
COLOR_SAND    = "#CCBFA0"
COLOR_SHADOW_GREEN = "#0a2015"
COLOR_BLUE_DECOR = "#2A4A9B"
COLOR_BLUE_TEXT = "#3A5AAB"

# Paleta de fontes:
FONT_TITLE    = ("Georgia", 22, "bold")
FONT_CARD     = ("Georgia", 18, "bold")
FONT_CARD_SM  = ("Georgia", 11)
FONT_LABEL    = ("Helvetica", 10, "bold")
FONT_BODY     = ("Helvetica", 10)
FONT_STATUS   = ("Helvetica", 9, "italic")
FONT_LOG      = ("Courier", 9)
FONT_SCORE    = ("Georgia", 14, "bold")


def naipe_simbolo(naipe_str: str) -> str:
    # Usado para o desenho do naipe da carta.
    mapa = {"OURO": "♦", "COPAS": "♥", "ESPADA": "♠", "PAUS": "♣"}
    for k, v in mapa.items():
        if k in naipe_str.upper():
            return v
    return "?"

def cor_naipe(naipe_str: str) -> str:
    naipe = naipe_str.upper()
    if naipe == "OURO" or naipe == "COPAS":
        return ACCENT_RED
    else: # PAUS ou ESPADA
        return TEXT_DARK 

def parse_carta(carta_str: str) -> tuple[str, str, str, str]:
    '''
    Faz o parse de *carta_str*, ou seja, pega o texto e retorna as características da carta.
    '''
    if carta_str == "?":
        return "?", "VERSO", "?", TEXT_LIGHT 
    try:
        partes = carta_str.split(" de ")
        val = partes[0].strip()
        nai = partes[1].strip() if len(partes) > 1 else ""
        return val, nai, naipe_simbolo(nai), cor_naipe(nai)
    except Exception:
        return "", "", "", TEXT_DARK


class CartaWidget(tk.Canvas):
    '''
    Classe que representa uma carta visual, ou seja, o desenho de uma carta
    baseada nas características de uma
    '''
    WIDTH = 80
    HEIGHT = 110

    def __init__(self, parent: tk.Widget, carta_str: str ="", selecionada: bool = False,
                 encoberta: bool = False, pequena: bool = False, **kw):
        """
        Inicializa o widget da carta visual com dimensões e estados iniciais.

        Argumentos:
            parent: O componente pai que conterá este canvas.
            carta_str: Texto que define o valor e naipe da carta.
            selecionada: Define se a carta inicia com destaque de seleção.
            encoberta: Define se a carta inicia virada para baixo.
            pequena: Se True, reduz o tamanho do widget em 30%.
            **kw: Argumentos nomeados adicionais repassados para a classe base tk.Canvas.
        """
        w = int(self.WIDTH * 0.7) if pequena else self.WIDTH
        h = int(self.HEIGHT * 0.7) if pequena else self.HEIGHT
        super().__init__(parent, width=w, height=h, bg=BG_FELT, highlightthickness=0, **kw)
        self.largura = w
        self.altura = h
        self.carta = carta_str
        self.selecionada = selecionada
        self.encoberta = encoberta
        self.pequena = pequena
        self._desenha()

    def _desenha(self):
        """
        Renderiza graficamente os elementos da carta no canvas.
        """
        # Limpa o desenho anterior
        self.delete("all")
        r = 6
        w, h = self.largura, self.altura

        self.create_rectangle(4, 4, w + 2, h + 2, fill=COLOR_SHADOW_GREEN, outline="", tags="sombra")

        bg = BG_CARD if not self.encoberta else BG_CARD_BACK
        borda = ACCENT_GOLD if self.selecionada else COLOR_SAND
        espessura = 3 if self.selecionada else 1
        self._rounded_rect(2, 2, w, h, r, fill=bg, outline=borda, width=espessura)

        # Desenha a carta quando está encoberta
        if self.encoberta:
            self._rounded_rect(8, 8, w - 6, h - 6, 4, fill="", outline=COLOR_BLUE_DECOR, width=1)
            self.create_text(w // 2, h // 2, text="🂠", font=("Arial", 20 if not self.pequena else 14), fill=COLOR_BLUE_TEXT)
            return

        val, _, simb, cor = parse_carta(self.carta)
        if not val:
            return

        # Tamanho do valor
        fs_val = 11 if self.pequena else 14
        # Tamanho do desenho do naipe
        fs_simb = 14 if self.pequena else 22
        pad = 5 # Padding

        # Desenha o valor no topo esquerdo - "nw"
        self.create_text(pad + 2, pad + 2, text=val,
                         font=("Georgia", fs_val, "bold"),
                         fill=cor, anchor="nw")
        
        # Desenha o naipe no topo esquerdo - "nw"
        self.create_text(pad + 2, pad + fs_val + 4, text=simb,
                         font=("Arial", fs_val - 2),
                         fill=cor, anchor="nw")

        # Desenha o naipe no centro - "center"
        self.create_text(w // 2, h // 2, text=simb,
                         font=("Arial", fs_simb, "bold"),
                         fill=cor, anchor="center")

        # Desenha o valor no canto inferior direito - "se"
        self.create_text(w - pad - 2, h - pad - 2, text=val,
                         font=("Georgia", fs_val, "bold"),
                         fill=cor, anchor="se")

    def _rounded_rect(self, x1: int, y1: int, x2: int, y2: int, r: int, **kw) -> int:
        """
        Desenha um retângulo com cantos arredondados utilizando polígonos suavizados.
        Retorna o ID do objeto canvas gerado pelo 'create_polygon'.

        Argumentos:
            x1 (int): Coordenada X do ponto superior esquerdo.
            y1 (int): Coordenada Y do ponto superior esquerdo.
            x2 (int): Coordenada X do ponto inferior direito.
            y2 (int): Coordenada Y do ponto inferior direito.
            r (int): Raio de curvatura dos cantos.
            **kw: Propriedades de estilização do Tkinter.
        """
        # Pontos usados para a criação de um polígono com os cantos arredondados.
        pts = [
            # Topo da carta
            (x1 + r, y1), (x2 - r, y1), (x2, y1),
            # Lado direito
            (x2, y1 + r), (x2, y2 - r), (x2, y2),
            # Base da carta
            (x2 - r, y2), (x1 + r, y2), (x1, y2),
            # Lado esquerdo
            (x1, y2 - r), (x1, y1 + r), (x1, y1)]
        return self.create_polygon(pts, smooth=True, **kw)

    def set_selecionada(self, v: bool):
        """
        Modifica o estado de seleção da carta e atualiza sua borda visual.
        """
        self.selecionada = v
        self._desenha()

    def set_carta(self, carta_str: str, encoberta: bool = False):
        """
        Atualiza o valor textual da carta e sua visibilidade, forçando o redesenho.
        """
        self.carta = carta_str
        self.encoberta = encoberta
        self._desenha()


class TrucoApp(tk.Tk):
    '''
    Representa o jogo em si para o jogador, ou seja, a conexão com o servidor, a entrada
    de dados e a exibição dos estados do jogo.
    '''
    def __init__(self):
        """
        Inicializa a aplicação do Truco, configura a janela principal e define os estados iniciais.
        """
        super().__init__()
        self.title("Truco Paulista")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)

        # Estado - Atributos privados
        self._sock: socket.socket | None = None
        self._shared_mem: SharedMemory | None = None
        self._meu_id: int = -1
        self._minha_vez: bool = False
        self._carta_selecionada: int = -1
        self._cartas_widgets: list[CartaWidget] = []
        self._cartas_nomes: list[str] = []
        self._ultimo_vez: int = -1
        self._conectado: bool = False
        self._running: bool = True
        self._ultimo_estado_ui = {}
        self._dialogo_truco = None
        self._receiver_thread = None
        self._estado_rodada: str = "NORMAL"
        self._quem_trucou: int = -1

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    
    def _build_ui(self):
        """
        Gera e organiza todos os elementos da interface gráfica.

        Divide o layout entre:
            -> topo (placar);
            -> corpo esquerdo (área verde do feltro da mesa, cartas jogadas, cartas da mão e botões de ação);
            -> painel direito (configurações de rede e terminal de logs).
        """
        # Inicia Topo - Barra de Placar
        top = tk.Frame(self, bg=BG_DARK, pady=6)
        top.pack(fill="x") # Ocupar toda a largura
        
        # Título principal do jogo fixado à esquerda
        tk.Label(top, text="♠  TRUCO PAULISTA  ♣", font=FONT_TITLE, fg=ACCENT_GOLD, bg=BG_DARK).pack(side="left", padx=16)
        
        # Placar dinâmico dos times fixado à direita
        self._lbl_placar = tk.Label(top, text="Time 1: 0  ×  0 :Time 2", font=FONT_SCORE, fg=TEXT_LIGHT, bg=BG_DARK)
        self._lbl_placar.pack(side="right", padx=16)

        # Linha horizontal dourada separadora entre o topo e o jogo
        tk.Frame(self, bg=ACCENT_GOLD, height=2).pack(fill="x")

        # Divide a tela em esquerda (Mesa) e direita (Painel)
        corpo = tk.Frame(self, bg=BG_FELT)
        corpo.pack(fill="both", expand=True)



        # Inicia Corpo Esquerdo - A Mesa do Jogo:
        mesa_frame = tk.Frame(corpo, bg=BG_FELT, padx=16, pady=12)
        mesa_frame.pack(side="left", fill="both", expand=True)

        # Desenho da vira:
        vira_row = tk.Frame(mesa_frame, bg=BG_FELT)
        vira_row.pack(anchor="w", pady=(0, 8))
        tk.Label(vira_row, text="VIRA:", font=FONT_LABEL,
                 fg=ACCENT_GOLD, bg=BG_FELT).pack(side="left", padx=(0, 8))
        
        # Widget da carta que define a manilha da rodada.
        self._vira_widget = CartaWidget(vira_row, pequena=True)
        self._vira_widget.pack(side="left")

        # Área das Cartas Descartadas (Mesa)
        tk.Label(mesa_frame, text="MESA", font=FONT_LABEL,
                 fg=ACCENT_GOLD, bg=BG_FELT).pack(anchor="w")
        
        # Espaço reservado para colocar os widgets das cartas que foram jogadas
        self._mesa_frame = tk.Frame(mesa_frame, bg=BG_FELT, pady=6)
        self._mesa_frame.pack(anchor="w")

        # Linha dourada
        tk.Frame(mesa_frame, bg=ACCENT_GOLD, height=1).pack(fill="x", pady=8)

        # Área das Cartas do Jogador
        tk.Label(mesa_frame, text="SUA MÃO", font=FONT_LABEL,
                 fg=ACCENT_GOLD, bg=BG_FELT).pack(anchor="w")
        
        # Espaço reservado para colocar as 3 cartas da mão de um jogador
        self._mao_frame = tk.Frame(mesa_frame, bg=BG_FELT, pady=6)
        self._mao_frame.pack(anchor="w")

        # Linha de Botões de Ação
        btn_row = tk.Frame(mesa_frame, bg=BG_FELT, pady=8)
        btn_row.pack(anchor="w")

        # Botão para descartar a carta selecionada aberta
        self._btn_jogar = self._btn(btn_row, "▶  JOGAR", BTN_GREEN, self._jogar)
        self._btn_jogar.pack(side="left", padx=(0, 8))

        # Botão para descartar a carta selecionada virada para baixo (coberta)
        self._btn_coberta = self._btn(btn_row, "👁  COBERTA", BG_CARD_BACK, self._jogar_coberta)
        self._btn_coberta.pack(side="left", padx=(0, 8))

        # Botão para pedir Truco / Seis / Nove / Doze
        self._btn_truco = self._btn(btn_row, "🗣  TRUCO!", BTN_TRUCO, self._pedir_truco)
        self._btn_truco.pack(side="left", padx=(0, 8))

        # Botão para sair da partida atual
        self._btn_sair = self._btn(btn_row, "✕  SAIR", BTN_RED_BG, self._sair)
        self._btn_sair.pack(side="left")

        # Desativa os botões até o jogo começar
        self._set_btns_ativos(False)

        # Barra de status inferior para mensagens contextuais
        self._lbl_status = tk.Label(mesa_frame, text="Conecte-se ao servidor para jogar.",
                                     font=FONT_STATUS, fg=TEXT_MUTED, bg=BG_FELT)
        self._lbl_status.pack(anchor="w", pady=(6, 0))


        # Inicia Corpo Direito - Rede e Logs:
        painel = tk.Frame(corpo, bg=BG_DARK, width=260, padx=12, pady=12)
        painel.pack(side="right", fill="y") # Fixação na lateral direita
        painel.pack_propagate(False) # Não muda de tamanho
        
        # Área de informações de rede:
        tk.Label(painel, text="CONEXÃO", font=FONT_LABEL,
                 fg=ACCENT_GOLD, bg=BG_DARK).pack(anchor="w")

        # Campos de IP e porta
        rede = tk.Frame(painel, bg=BG_DARK)
        rede.pack(fill="x", pady=(4, 8))

        # Rótulo para o Endereço de IP
        tk.Label(rede, text="IP:", font=FONT_BODY, fg=TEXT_LIGHT, bg=BG_DARK).grid(row=0, column=0, sticky="w")
        self._entry_ip = tk.Entry(rede, font=FONT_BODY, width=14, bg=COLOR_SHADOW_GREEN, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT, relief="flat", bd=4)
        self._entry_ip.insert(0, "127.0.0.1") # IP padrão
        self._entry_ip.grid(row=0, column=1, padx=(4, 0))

        # Rótulo para a porta de rede
        tk.Label(rede, text="Porta:", font=FONT_BODY, fg=TEXT_LIGHT, bg=BG_DARK).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._entry_porta = tk.Entry(rede, font=FONT_BODY, width=6, bg=COLOR_SHADOW_GREEN, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT, relief="flat", bd=4)
        self._entry_porta.insert(0, "5555") # Porta padrão
        self._entry_porta.grid(row=1, column=1, padx=(4, 0))

        # Botão que dispara o início da conexão
        self._btn_conectar = self._btn(painel, "⚡  CONECTAR", BTN_GREEN, self._conectar)
        self._btn_conectar.pack(fill="x", pady=(0, 10))

        # Identificador de jogador
        self._lbl_id = tk.Label(painel, text="Seu ID: —", font=FONT_LABEL, fg=TEXT_LIGHT, bg=BG_DARK)
        self._lbl_id.pack(anchor="w")
        
        # Indicador de vez
        self._lbl_vez_ind = tk.Label(painel, text="", font=("Helvetica", 11, "bold"), fg=BTN_GREEN, bg=BG_DARK)
        self._lbl_vez_ind.pack(anchor="w", pady=(2, 8))

        # Linha horizontal que separa as informações e os logs.
        tk.Frame(painel, bg=ACCENT_GOLD, height=1).pack(fill="x", pady=(0, 6))
        
        # Área de Logs
        tk.Label(painel, text="LOG", font=FONT_LABEL, fg=ACCENT_GOLD, bg=BG_DARK).pack(anchor="w")
        log_frame = tk.Frame(painel, bg=BG_DARK)
        log_frame.pack(fill="both", expand=True, pady=(4, 0))
        
        # Histórico de acontecimentos
        self._txt_log = tk.Text(log_frame, font=FONT_LOG, bg=COLOR_SHADOW_GREEN, fg=TEXT_MUTED, state="disabled", wrap="word", bd=0, relief="flat", height=20, width=28)
        
        # Cria o deslizamento na área de logs.
        sb = ttk.Scrollbar(log_frame, command=self._txt_log.yview)
        self._txt_log.configure(yscrollcommand=sb.set)
        self._txt_log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")



    def _btn(self, parent: tk.Widget, texto: str, cor: str, cmd) -> tk.Button:
        """
        Cria um botão.

        Argumentos:
            parent: O pai do botão.
            texto: O rótulo visível no botão.
            cor: Código hexadecimal ou nome da cor de fundo.
            cmd: Função executada no clique do botão.
        """
        b: tk.Button = tk.Button(parent, text=texto, font=FONT_LABEL,
            bg=cor, fg=TEXT_LIGHT, relief="flat",
            padx=10, pady=6, cursor="hand2",
            activebackground=BTN_HOVER,
            activeforeground=TEXT_DARK,
            command=cmd)
        return b

    
    def _conectar(self):
        """
        Inicia o processo de conexão disparando uma thread.
        Valida se o cliente já está conectado para evitar conexões duplicadas.
        Extrai o IP e a Porta inseridos nos campos de entrada.
        """
        if self._conectado:
            self._log("Já conectado.")
            return
        ip = self._entry_ip.get().strip()
        porta = int(self._entry_porta.get().strip())
        threading.Thread(target=self._thread_conectar, args=(ip, porta), daemon=True).start()

    def _thread_conectar(self, ip: str, porta: int):
        """
        Executa a conexão com o servidor via socket.
        Estabelece o socket, decodifica a mensagem de boas-vindas do servidor para 
        extrair o ID do jogador, tenta vincular o segmento de SharedMemory ("MesaTruco") 
        e inicia os loops de controle da partida.
        """
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10)
            self._sock.connect((ip, porta))

            boas_vindas = self._sock.recv(1024).decode("utf-8")
            # Recupera o ID pela mensagem de boas vindas
            self._meu_id = int(boas_vindas.strip().split()[-1])
            self._log(f"✓ Conectado! {boas_vindas.strip()}")

            try:
                self._shared_mem = SharedMemory("MesaTruco", False)
            except Exception as e:
                self._log(f"Memória compartilhada: {e}")

            self._conectado = True
            self.after(0, self._on_conectado)
            self._loop_jogo()

        except Exception as e:
            self._log(f"✗ Erro: {e}")

    def _on_conectado(self):
        """
        Modifica os componentes gráficos após o sucesso da conexão de rede.

        Desativa o botão de conexão, atualiza o rótulo com o ID do jogador e 
        dispara a thread secundária `_receiver_loop` voltada a escutar o socket.
        """
        self._lbl_id.config(text=f"Seu ID: {self._meu_id}")
        self._btn_conectar.config(state="disabled", text="Conectado!")
        self._log("Aguardando o jogo iniciar...")
        self._receiver_thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self._receiver_thread.start()

    
    def _receiver_loop(self):
        """
        Loop em thread separada responsável por escutar continuamente dados vindos do socket.

        Enquanto o jogo estiver rodando, captura strings do servidor e delega de forma 
        segura à thread principal do Tkinter after(0, ...) o processamento das regras de negócio.
        """
        while self._running and self._conectado:
            try:
                data = self._sock.recv(1024).decode()
                if not data:
                    break
                # Agenda a execução de _processa_mensagem na thread principal do Tkinter assim que possível.
                self.after(0, self._processa_mensagem, data) 
            except Exception as e:
                continue

    def _processa_mensagem(self, msg: str):
        """
        Interpreta comandos e eventos de rede recebidos do servidor.

        Trata confirmações de jogadas, distribuição de novas cartas, requisições de 
        truco de oponentes, encerramento de partidas e mensagens de erro.

        Argumento:
            msg: Mensagem textual vinda do servidor.
        """
        msg = msg.strip()

        if "JOGADA_OK" in msg:
            self._log("✓ Comando executado com sucesso.")
        elif "Cartas:" in msg:
            self._log(" *** Recebendo novas cartas...")
            inicio = msg.find("Cartas:")
            fim = msg.find("]", inicio)
            if inicio != -1 and fim != -1:
                mensagem_limpa = msg[inicio:fim + 1]
            else:
                mensagem_limpa = msg[inicio:]
            try:
                self._recebe_cartas(mensagem_limpa)
            except Exception as e:
                self._log(f"Erro ao processar cartas: {e}")
        elif "TRUCO_PEDIDO:" in msg:
            try:
                parte = msg[msg.find("TRUCO_PEDIDO:"):]
                valor = int(parte.split(":")[1].split()[0])
                self._mostrar_dialogo_truco(valor)
            except Exception as e:
                self._log(f"Erro ao interpretar pedido de truco: {e}")
        elif "FIM_DE_JOGO:" in msg:
            self._log(msg)
            self._set_btns_ativos(False)
            self._minha_vez = False
            messagebox.showinfo("Fim de jogo", msg)
        elif "COMANDO_INVALIDO" in msg:
            self._log("✗ Comando inválido.")
        else:
            self._log(f"{msg}")

    
    def _loop_jogo(self):
        """
        Loop executado em segundo plano para inspecionar a memória compartilhada.

        Lê a estrutura da mesa a cada 100ms e computa se o turno atual de jogo 
        pertence ao usuário local baseado na variável _meu_id.
        """
        while self._running and self._conectado:
            estado = self._ler_estado()
            if estado:
                self._quem_trucou = estado.get("quem_trucou")
                self.after(0, self._atualiza_ui, estado)
                eh_minha_vez = estado["vez"] == self._meu_id
                estado_normal = estado.get("estado_rodada") == "NORMAL"
                if eh_minha_vez and estado_normal:
                    self.after(0, self._set_minha_vez, True)
                else:
                    self.after(0, self._set_minha_vez, False)
            time.sleep(0.1)

    
    def _atualiza_ui(self, estado: dict):
        """
        Atualiza o estado visual da interface gráfica baseado em um dicionário de estados.

        Evita renderizações desnecessárias se o estado for idêntico ao último. Atualiza 
        os rótulos de placar, número de quedas, pontuação em jogo da rodada, a carta do 
        Vira e reconstrói as cartas da mesa central.

        Argumento:
            estado: Dicionário contendo dados extraídos da memória compartilhada.
        """
        if self._ultimo_estado_ui == estado:
            return
        self._ultimo_estado_ui = estado

        # Estado vazio = rodada não começou
        if not estado or "vira" not in estado:
            self._log("Aguardando início da rodada pelo servidor...")
            return

        # Atualiza o texto do placar no topo da tela
        self._lbl_placar.config(text=estado.get("placar", "Esperando..."))

        # Atualiza a vira.
        vira_str = estado.get("vira", "")
        self._vira_widget.set_carta(vira_str)

        self._estado_rodada = estado.get("estado_rodada", "NORMAL")

        self._desenha_mesa(estado.get("mesa", {}))

    def _desenha_mesa(self, mesa: dict):
        """
        Limpa e redesenha a região central de cartas jogadas na mesa.

        Gera cartas em miniatura dinamicamente para cada carta revelada 
        ou coberta que foi jogada pelos participantes.

        Argumento:
            mesa (dict): Mapeamento de IDs de jogadores para as propriedades das suas cartas na mesa.
        """
        # Limpeza da mesa anterior.
        # O método 'winfo_children' retorna as CartasWidget da mesa.
        for w in self._mesa_frame.winfo_children():
            w.destroy()
        
        # Sem nenhuma jogada:
        if not mesa:
            tk.Label(self._mesa_frame, text="Mesa vazia — ninguém jogou ainda.",
                     font=FONT_STATUS, fg=TEXT_MUTED, bg=BG_FELT).pack()
            return
        
        for id_jog, dados in mesa.items():
            base = tk.Frame(self._mesa_frame, bg=BG_FELT, padx=6)
            base.pack(side="left")
            tk.Label(base, text=f"J {id_jog}", font=FONT_STATUS,
                     fg=TEXT_MUTED, bg=BG_FELT).pack()
            enc = dados.get("encoberta", False)
            
            # Desenha a carta
            cw = CartaWidget(base, dados.get("carta", "?"), False, enc, True)
            cw.pack()
            
            # Texto com a descrição da carta abaixo dela.
            tk.Label(base, text=dados.get("carta", "?"),
                     font=FONT_STATUS, fg=TEXT_LIGHT, bg=BG_FELT).pack()


    def _recebe_cartas(self, dados: str):
        """
        Processa e extrai a lista de strings com os nomes das cartas enviadas pelo servidor.
        Limpa a seleção atual, armazena as novas cartas locais e aciona o redesenho da mão.
        """
        try:
            linha = dados.strip()
            inicio = linha.find("[")
            fim = linha.find("]")
            if inicio != -1 and fim != -1:
                dentro = linha[inicio + 1:fim]
                self._cartas_nomes = [] # Torna a lista de cartas vazia.
                cartas = dentro.split(",")
                for c in cartas:
                    carta_limpa = c.strip()
                    self._cartas_nomes.append(carta_limpa)
            else:
                self._cartas_nomes = []
        except Exception:
            self._cartas_nomes = []

        self._carta_selecionada = -1
        self._desenha_mao()
        self._log(f"Suas cartas: {self._cartas_nomes}")


    def _desenha_mao(self):
        """
        Destrói e reconstrói os componentes gráficos da mão de cartas do jogador.
        """
        # Limpeza da mão anterior.
        for w in self._mao_frame.winfo_children():
            w.destroy()
        self._cartas_widgets = []

        for i, nome in enumerate(self._cartas_nomes):
            frame = tk.Frame(self._mao_frame, bg=BG_FELT, padx=4)
            frame.pack(side="left")
            # Desenha a mão do jogador:
            cw = CartaWidget(frame, carta_str=nome, selecionada=(i == self._carta_selecionada))
            cw.pack()
            # Button-1 = Clique do botão esquerdo
            cw.bind("<Button-1>", self._cria_evento_clique(i)) # Precisa que o segundo argumento seja função.
            tk.Label(frame, text=nome, font=("Helvetica", 8),
                     fg=TEXT_MUTED, bg=BG_FELT, wraplength=85).pack()
            self._cartas_widgets.append(cw)

    # Retorna uma função.
    def _cria_evento_clique(self, idx: int):
        '''
        Cria a mecânica de mostrar a seleção da carta com índice *idx*.
        '''
        def aux(evento):
            self._seleciona_carta(idx)
        return aux
        
    def _seleciona_carta(self, idx: int):
        """
        Gerencia o índice da carta atualmente escolhida para ser jogada.
        A seleção é permitida apenas se for o turno do usuário e se não houver um pedido 
        de truco pendente de resposta. Atualiza o contorno visual da carta selecionada.
        """
        if not self._minha_vez or self._estado_rodada != "NORMAL":
            return
        self._carta_selecionada = idx
        # Loop para ver qual a carta que se deve selecionar.
        i: int = 0
        while i < len(self._cartas_widgets):
            cw = self._cartas_widgets[i]
            cw.set_selecionada(i == idx)
            i += 1
        self._log(f"Carta selecionada: [{idx}] {self._cartas_nomes[idx]}")

    def _set_minha_vez(self, v: bool):
        """
        Modifica a permissão de turno do jogador e altera os rótulos informativos de status.

        Ativa ou desativa os botões de ação e exibe orientações ao usuário no rodapé,
        baseando-se no fato do jogador possuir ou não cartas ou estar em meio a um aumento de aposta de Truco.

        Argumento:
            v: True se passou a ser a vez do jogador atual, False caso contrário.
        """
        self._minha_vez = v
        tem_cartas = self._cartas_nomes != []
        ativo = v and tem_cartas and self._estado_rodada == "NORMAL"
        self._set_btns_ativos(ativo)
        if ativo:
            self._lbl_status.config(text=" Sua vez! Selecione uma carta e jogue.", fg=BTN_GREEN)
        elif v and not tem_cartas:
            self._lbl_status.config(text=" Aguardando suas cartas...", fg=TEXT_MUTED)
        elif v and self._estado_rodada != "NORMAL":
            self._lbl_status.config(text=" Aguardando resposta do adversário...", fg=TEXT_MUTED)
        else:
            self._lbl_status.config(text="Aguardando a jogada do adversário...", fg=TEXT_MUTED)


    def _set_btns_ativos(self, ativo: bool):
        """
        Altera o estado funcional dos botões de interação do jogo (Jogar, Coberta, Truco).
        """
        estado = "normal" if ativo else "disabled"
        self._btn_jogar.config(state=estado)
        self._btn_coberta.config(state=estado)
         
        meu_time_pediu = False
        if self._quem_trucou != -1:
            meu_time_pediu = (self._quem_trucou % 2) == (self._meu_id % 2)
            
        pode_trucar = ativo and not meu_time_pediu
        estado_truco = "normal" if pode_trucar else "disabled"
        
        self._btn_truco.config(state=estado_truco)

    
    def _remover_carta_local(self, idx: int):
        """
        Elimina uma carta da coleção interna do cliente e reorganiza a mão.

        Argumento:
            idx (int): Posição da lista da carta que deve ser desfeita.
        """
        if 0 <= idx < len(self._cartas_nomes):
            self._cartas_nomes.pop(idx)
            self._carta_selecionada = -1
            self._desenha_mao()

    def _jogar(self):
        """
        Dispara a ação de jogar a carta selecionada aberta.

        Verifica pré-condições de validação como checar se uma carta foi previamente
        clicada e se a rodada não se encontra congelada devido a uma chamada de truco.
        """
        if self._carta_selecionada < 0:
            messagebox.showwarning("Selecione uma carta",
                                   "Clique em uma carta antes de jogar.")
            return
        if self._estado_rodada != "NORMAL":
            self._log("Aguardando resposta do truco, não pode jogar agora.")
            return
        idx = self._carta_selecionada
        self._remover_carta_local(idx)
        self._enviar_comando(f"JOGAR:{idx}")

    def _jogar_coberta(self):
        """
        Dispara a ação de ocultar e jogar a carta selecionada de forma coberta.
        Seguem as mesmas restrições e validações do método _jogar.
        """
        if self._carta_selecionada < 0:
            messagebox.showwarning("Selecione uma carta",
                                   "Clique em uma carta antes de jogar coberta.")
            return
        if self._estado_rodada != "NORMAL":
            self._log("Aguardando resposta do truco, não pode jogar agora.")
            return
        idx = self._carta_selecionada
        self._remover_carta_local(idx)
        self._enviar_comando(f"JOGAR:{idx}:COBERTA")

    def _pedir_truco(self):
        """
        Envia a string de aumento de pontos ("TRUCO") para o servidor de jogos.
        """
        if self._estado_rodada != "NORMAL":
            self._log("Não é possível pedir truco agora.")
            return
        self._enviar_comando("TRUCO")

    def _sair(self):
        """
        Oferece ao usuário uma confirmação para abandonar o jogo ativo.

        Em caso positivo, notifica o servidor e fecha os recursos da aplicação.
        """
        if messagebox.askyesno("Sair", "Deseja abandonar a partida?"):
            self._enviar_comando("SAIR")
            self._on_close()

    def _enviar_comando(self, cmd: str):
        """
        Envia comando para o servidor pelo socket.
        Argumento:
            cmd (str): O texto com o comando no formato esperado pelo protocolo (ex: "JOGAR:1").
        """
        if not self._sock or not self._minha_vez:
            return
        try:
            self._sock.send(cmd.encode())
            self._log(f"▶ Enviado: {cmd}")
            self._set_btns_ativos(False)
            self._minha_vez = False
        except Exception as e:
            self._log(f"✗ Erro ao enviar: {e}")

    
    def _mostrar_dialogo_truco(self, valor: int):
        """
        Gera uma janela suspensa que força o jogador a responder ao Truco.
        Argumento:
            valor (int): O valor atual em pontos da rodada até o momento.
        """
        if self._dialogo_truco is not None:
            return
        # Criação de uma janela:
        top = tk.Toplevel(self)
        top.title("Truco!")
        top.geometry("300x150")
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()
        tk.Label(top, text=f"O adversário pediu truco!\n Valor atual da rodada: {valor} ponto(s)",
                 font=FONT_BODY, padx=10, pady=10).pack()
        frame = tk.Frame(top)
        frame.pack(pady=10)
        # Funções Lambda para facilitar a organização
        btn_aceitar = tk.Button(frame, text="Aceitar", command=lambda: self._responde_truco(True, top),
                                bg=BTN_GREEN, fg=TEXT_LIGHT, padx=15, pady=5)
        btn_aceitar.pack(side="left", padx=10)
        btn_correr = tk.Button(frame, text="Correr", command=lambda: self._responde_truco(False, top),
                               bg=BTN_RED_BG, fg=TEXT_LIGHT, padx=15, pady=5)
        btn_correr.pack(side="left", padx=10)
        self._dialogo_truco = top

    def _responde_truco(self, aceitou: bool, janela: tk.Toplevel):
        """
        Envia a resposta de contra-proposta de truco selecionada na modal de diálogo.
        Destrói a janela de diálogo imediatamente após o clique e envia "ACEITAR" ou "CORRER".
        """
        janela.destroy()
        self._dialogo_truco = None

        if not self._sock:
            return

        try:
            if aceitou:
                self._sock.send(b"ACEITAR")
                self._log("▶ Resposta enviada: ACEITAR")
            else:
                self._sock.send(b"CORRER")
                self._log("▶ Resposta enviada: CORRER")
        except Exception as e:
            self._log(f"✗ Erro ao responder truco: {e}")

    
    def _ler_estado(self) -> dict | None:
        """
        Acessa e decodifica a memória compartilhada para retornar o estado atual do jogo.
        """
        if not self._shared_mem:
            return None
        try:
            dados_brutos = bytes(self._shared_mem.buf[:1024]).decode("utf-8").strip()
            return json.loads(dados_brutos)
        except Exception:
            return None

    def _inner(self, msg: str): 
        self._txt_log.config(state="normal")
        ts = time.strftime("%H:%M:%S")  # Obtém o horário atual no formato HH:MM:SS.
        self._txt_log.insert("end", f"[{ts}] {msg}\n")
        self._txt_log.see("end")  # Faz a rolagem automática para a última linha inserida.
        self._txt_log.config(state="disabled") # Agenda a atualização da interface para a thread principal do Tkinter.
        
    def _log(self, msg: str):
        """
        Escreve  uma linha informativa no campo de logs textuais.
        """ 
        # A execução da escrita é agendada para quando for possível.
        self.after(0, self._inner, msg)

        
    def _on_close(self):
        """
        Fecha e desaloca todos os recursos abertos pela aplicação no sistema operacional.
        """
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        if self._shared_mem:
            try:
                self._shared_mem.close()
            except Exception:
                pass
        self.destroy()



if __name__ == "__main__":
    app = TrucoApp()
    app.mainloop()
    
    
    
    
    