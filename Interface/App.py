"""
cliente_gui.py — Interface Tkinter para o jogo de Truco
Substitui o cliente.py original com uma UI visual completa.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import time
import threading
from multiprocessing.shared_memory import SharedMemory


# ─────────────────────────── Paleta ───────────────────────────
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

FONT_TITLE    = ("Georgia", 22, "bold")
FONT_CARD     = ("Georgia", 18, "bold")
FONT_CARD_SM  = ("Georgia", 11)
FONT_LABEL    = ("Helvetica", 10, "bold")
FONT_BODY     = ("Helvetica", 10)
FONT_STATUS   = ("Helvetica", 9, "italic")
FONT_LOG      = ("Courier", 9)
FONT_SCORE    = ("Georgia", 14, "bold")


def naipe_simbolo(naipe_str: str) -> str:
    mapa = {"OURO": "♦", "COPAS": "♥", "ESPADA": "♠", "PAUS": "♣"}
    for k, v in mapa.items():
        if k in naipe_str.upper():
            return v
    return "?"

def cor_naipe(naipe_str: str) -> str:
    if any(n in naipe_str.upper() for n in ("OURO", "COPAS")):
        return ACCENT_RED
    return TEXT_DARK

def parse_carta(carta_str: str):
    if carta_str == "?":
        return "?", "VERSO", "?", TEXT_LIGHT
    try:
        partes = carta_str.split(" de ")
        val = partes[0].strip()
        nai = partes[1].strip() if len(partes) > 1 else ""
        return val, nai, naipe_simbolo(nai), cor_naipe(nai)
    except Exception:
        return carta_str, "", "", TEXT_DARK


# ─────────────────────────── Widget Carta ───────────────────────────
class CartaWidget(tk.Canvas):
    WIDTH, HEIGHT = 80, 110

    def __init__(self, parent, carta_str="", selecionada=False,
                 encoberta=False, pequena=False, **kw):
        w = int(self.WIDTH * 0.7) if pequena else self.WIDTH
        h = int(self.HEIGHT * 0.7) if pequena else self.HEIGHT
        super().__init__(parent, width=w, height=h,
                         bg=BG_FELT, highlightthickness=0, **kw)
        self.largura = w
        self.altura = h
        self._carta = carta_str
        self._selecionada = selecionada
        self._encoberta = encoberta
        self._pequena = pequena
        self._desenha()

    def _desenha(self):
        self.delete("all")
        r = 6
        w, h = self.largura, self.altura

        self.create_rectangle(4, 4, w + 2, h + 2,
                               fill="#0a2015", outline="", tags="sombra")

        bg = BG_CARD if not self._encoberta else BG_CARD_BACK
        borda = ACCENT_GOLD if self._selecionada else "#CCBFA0"
        espessura = 3 if self._selecionada else 1
        self._rounded_rect(2, 2, w, h, r, fill=bg,
                            outline=borda, width=espessura)

        if self._encoberta:
            self._rounded_rect(8, 8, w - 6, h - 6, 4,
                                fill="", outline="#2A4A9B", width=1)
            self.create_text(w // 2, h // 2, text="🂠",
                              font=("Arial", 20 if not self._pequena else 14),
                              fill="#3A5AAB")
            return

        val, nai, simb, cor = parse_carta(self._carta)
        if not val:
            return

        fs_val = 11 if self._pequena else 14
        fs_simb = 14 if self._pequena else 22
        pad = 5

        self.create_text(pad + 2, pad + 2, text=val,
                         font=("Georgia", fs_val, "bold"),
                         fill=cor, anchor="nw")
        self.create_text(pad + 2, pad + fs_val + 4, text=simb,
                         font=("Arial", fs_val - 2),
                         fill=cor, anchor="nw")

        self.create_text(w // 2, h // 2, text=simb,
                         font=("Arial", fs_simb, "bold"),
                         fill=cor, anchor="center")

        self.create_text(w - pad - 2, h - pad - 2, text=val,
                         font=("Georgia", fs_val, "bold"),
                         fill=cor, anchor="se")

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1,
               x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2,
               x1, y2 - r, x1, y1 + r, x1, y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def set_selecionada(self, v: bool):
        self._selecionada = v
        self._desenha()

    def set_carta(self, carta_str: str, encoberta=False):
        self._carta = carta_str
        self._encoberta = encoberta
        self._desenha()


# ─────────────────────────── App Principal ───────────────────────────
class TrucoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Truco Paulista")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)

        # Estado
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

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── Construção UI ───
    def _build_ui(self):
        top = tk.Frame(self, bg=BG_DARK, pady=6)
        top.pack(fill="x")
        tk.Label(top, text="♠  TRUCO PAULISTA  ♣",
                 font=FONT_TITLE, fg=ACCENT_GOLD, bg=BG_DARK).pack(side="left", padx=16)
        self._lbl_placar = tk.Label(top, text="Time 1: 0  ×  Time 2: 0",
                                     font=FONT_SCORE, fg=TEXT_LIGHT, bg=BG_DARK)
        self._lbl_placar.pack(side="right", padx=16)

        tk.Frame(self, bg=ACCENT_GOLD, height=2).pack(fill="x")

        corpo = tk.Frame(self, bg=BG_FELT)
        corpo.pack(fill="both", expand=True)

        mesa_frame = tk.Frame(corpo, bg=BG_FELT, padx=16, pady=12)
        mesa_frame.pack(side="left", fill="both", expand=True)

        vira_row = tk.Frame(mesa_frame, bg=BG_FELT)
        vira_row.pack(anchor="w", pady=(0, 8))
        tk.Label(vira_row, text="VIRA:", font=FONT_LABEL,
                 fg=ACCENT_GOLD, bg=BG_FELT).pack(side="left", padx=(0, 8))
        self._vira_widget = CartaWidget(vira_row, pequena=True)
        self._vira_widget.pack(side="left")
        self._lbl_vira_txt = tk.Label(vira_row, text="",
                                       font=FONT_BODY, fg=TEXT_LIGHT, bg=BG_FELT)
        self._lbl_vira_txt.pack(side="left", padx=8)

        info_row = tk.Frame(mesa_frame, bg=BG_FELT)
        info_row.pack(anchor="w", pady=(0, 10))
        self._lbl_queda = tk.Label(info_row, text="Queda: 1ª",
                                    font=FONT_LABEL, fg=TEXT_MUTED, bg=BG_FELT)
        self._lbl_queda.pack(side="left", padx=(0, 20))
        self._lbl_valor = tk.Label(info_row, text="Valor: 1 pt",
                                    font=FONT_LABEL, fg=TEXT_MUTED, bg=BG_FELT)
        self._lbl_valor.pack(side="left")

        tk.Label(mesa_frame, text="MESA", font=FONT_LABEL,
                 fg=ACCENT_GOLD, bg=BG_FELT).pack(anchor="w")
        self._mesa_frame = tk.Frame(mesa_frame, bg=BG_FELT, pady=6)
        self._mesa_frame.pack(anchor="w")

        tk.Frame(mesa_frame, bg=ACCENT_GOLD, height=1).pack(fill="x", pady=8)

        tk.Label(mesa_frame, text="SUA MÃO", font=FONT_LABEL,
                 fg=ACCENT_GOLD, bg=BG_FELT).pack(anchor="w")
        self._mao_frame = tk.Frame(mesa_frame, bg=BG_FELT, pady=6)
        self._mao_frame.pack(anchor="w")

        btn_row = tk.Frame(mesa_frame, bg=BG_FELT, pady=8)
        btn_row.pack(anchor="w")

        self._btn_jogar = self._btn(btn_row, "▶  JOGAR", BTN_GREEN, self._jogar)
        self._btn_jogar.pack(side="left", padx=(0, 8))

        self._btn_coberta = self._btn(btn_row, "👁  COBERTA", BG_CARD_BACK, self._jogar_coberta)
        self._btn_coberta.pack(side="left", padx=(0, 8))

        self._btn_truco = self._btn(btn_row, "🗣  TRUCO!", BTN_TRUCO, self._pedir_truco)
        self._btn_truco.pack(side="left", padx=(0, 8))

        self._btn_sair = self._btn(btn_row, "✕  SAIR", BTN_RED_BG, self._sair)
        self._btn_sair.pack(side="left")

        self._set_btns_ativos(False)

        self._lbl_status = tk.Label(mesa_frame, text="Conecte-se ao servidor para jogar.",
                                     font=FONT_STATUS, fg=TEXT_MUTED, bg=BG_FELT)
        self._lbl_status.pack(anchor="w", pady=(6, 0))

        painel = tk.Frame(corpo, bg=BG_DARK, width=260, padx=12, pady=12)
        painel.pack(side="right", fill="y")
        painel.pack_propagate(False)

        tk.Label(painel, text="CONEXÃO", font=FONT_LABEL,
                 fg=ACCENT_GOLD, bg=BG_DARK).pack(anchor="w")

        conn_grid = tk.Frame(painel, bg=BG_DARK)
        conn_grid.pack(fill="x", pady=(4, 8))

        tk.Label(conn_grid, text="IP:", font=FONT_BODY,
                 fg=TEXT_LIGHT, bg=BG_DARK).grid(row=0, column=0, sticky="w")
        self._entry_ip = tk.Entry(conn_grid, font=FONT_BODY, width=14,
                                   bg="#0E2418", fg=TEXT_LIGHT,
                                   insertbackground=TEXT_LIGHT,
                                   relief="flat", bd=4)
        self._entry_ip.insert(0, "127.0.0.1")
        self._entry_ip.grid(row=0, column=1, padx=(4, 0))

        tk.Label(conn_grid, text="Porta:", font=FONT_BODY,
                 fg=TEXT_LIGHT, bg=BG_DARK).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._entry_porta = tk.Entry(conn_grid, font=FONT_BODY, width=6,
                                      bg="#0E2418", fg=TEXT_LIGHT,
                                      insertbackground=TEXT_LIGHT,
                                      relief="flat", bd=4)
        self._entry_porta.insert(0, "5555")
        self._entry_porta.grid(row=1, column=1, padx=(4, 0), pady=(4, 0), sticky="w")

        self._btn_conectar = self._btn(painel, "⚡  CONECTAR", BTN_GREEN, self._conectar)
        self._btn_conectar.pack(fill="x", pady=(0, 10))

        self._lbl_id = tk.Label(painel, text="Seu ID: —",
                                  font=FONT_LABEL, fg=TEXT_LIGHT, bg=BG_DARK)
        self._lbl_id.pack(anchor="w")
        self._lbl_vez_ind = tk.Label(painel, text="",
                                      font=("Helvetica", 11, "bold"),
                                      fg=BTN_GREEN, bg=BG_DARK)
        self._lbl_vez_ind.pack(anchor="w", pady=(2, 8))

        tk.Frame(painel, bg=ACCENT_GOLD, height=1).pack(fill="x", pady=(0, 6))
        tk.Label(painel, text="LOG", font=FONT_LABEL,
                 fg=ACCENT_GOLD, bg=BG_DARK).pack(anchor="w")
        log_frame = tk.Frame(painel, bg=BG_DARK)
        log_frame.pack(fill="both", expand=True, pady=(4, 0))
        self._txt_log = tk.Text(log_frame, font=FONT_LOG, bg="#0A1A10",
                                 fg=TEXT_MUTED, state="disabled",
                                 wrap="word", bd=0, relief="flat",
                                 height=20, width=28)
        sb = ttk.Scrollbar(log_frame, command=self._txt_log.yview)
        self._txt_log.configure(yscrollcommand=sb.set)
        self._txt_log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _btn(self, parent, texto, cor, cmd):
        b = tk.Button(parent, text=texto, font=FONT_LABEL,
                      bg=cor, fg=TEXT_LIGHT, relief="flat",
                      padx=10, pady=6, cursor="hand2",
                      activebackground=BTN_HOVER,
                      activeforeground=TEXT_DARK,
                      command=cmd)
        return b

    # ─── Conexão ───
    def _conectar(self):
        if self._conectado:
            self._log("Já conectado.")
            return
        ip = self._entry_ip.get().strip()
        porta = int(self._entry_porta.get().strip())
        threading.Thread(target=self._thread_conectar,
                         args=(ip, porta), daemon=True).start()

    def _thread_conectar(self, ip, porta):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(10)
            self._sock.connect((ip, porta))

            boas_vindas = self._sock.recv(1024).decode("utf-8")
            self._meu_id = int(boas_vindas.strip().split()[-1])
            self._log(f"✓ Conectado! {boas_vindas.strip()}")

            try:
                self._shared_mem = SharedMemory("MesaTruco", False)
            except Exception as e:
                self._log(f"⚠ Memória compartilhada: {e}")

            self._conectado = True
            self.after(0, self._on_conectado)
            self._loop_jogo()

        except Exception as e:
            self._log(f"✗ Erro: {e}")

    def _on_conectado(self):
        self._lbl_id.config(text=f"Seu ID: {self._meu_id}")
        self._btn_conectar.config(state="disabled", text="Conectado")
        self._log("Aguardando o jogo iniciar...")
        self._receiver_thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self._receiver_thread.start()

    # ─── Receiver de mensagens do servidor ───
    def _receiver_loop(self):
        while self._running and self._conectado:
            try:
                data = self._sock.recv(1024).decode()
                if not data:
                    break
                self.after(0, self._processa_mensagem, data)
            except Exception as e:
                self.after(0, self._log, f"Erro no receiver: {e}")
                break

    def _processa_mensagem(self, msg: str):
        msg = msg.strip()
        
        # 1. Trata JOGADA_OK, que pode vir colado com as Cartas
        if "JOGADA_OK" in msg:
            self._log("✓ Comando executado com sucesso.")

        # 2. Trata recebimento de Cartas usando 'in'
        if "Cartas:" in msg:
            self._log("📨 Recebendo novas cartas...")
            
            # Corta do 'C' de Cartas até o ']' do final da lista
            inicio = msg.find("Cartas:")
            fim = msg.find("]", inicio)
            
            if inicio != -1 and fim != -1:
                mensagem_limpa = msg[inicio:fim + 1]
            else:
                mensagem_limpa = msg[inicio:] # Fallback caso falte o colchete
                
            try:
                self._recebe_cartas(mensagem_limpa)
                
                # Reavalia a vez lendo a memória
                estado = self._ler_estado()
                if estado and estado.get("vez") == self._meu_id:
                    self._set_minha_vez(True)
            except Exception as e:
                self._log(f"Erro interno ao processar cartas: {e}")

        # 3. Trata pedido de Truco
        if "TRUCO_PEDIDO:" in msg:
            try:
                # Corta a string a partir de TRUCO_PEDIDO para evitar lixo no começo
                parte = msg[msg.find("TRUCO_PEDIDO:"):]
                valor = int(parte.split(":")[1].split()[0])
                self._mostrar_dialogo_truco(valor)
            except Exception as e:
                self._log(f"Erro ao interpretar pedido de truco: {e}")

        # 4. Trata Fim de Jogo
        if "FIM_DE_JOGO:" in msg:
            self._log(f"🏁 {msg}")
            self._set_btns_ativos(False)
            self._minha_vez = False
            messagebox.showinfo("Fim de jogo", msg)

        # 5. Outros
        if "COMANDO_INVALIDO" in msg:
            self._log("✗ Comando inválido.")
            
        # 6. Só cai aqui se for uma mensagem completamente desconhecida
        if not any(x in msg for x in ["JOGADA_OK", "Cartas:", "TRUCO_PEDIDO:", "FIM_DE_JOGO:", "COMANDO_INVALIDO"]):
            self._log(f"{msg}")

    # ─── Loop principal de jogo (monitora a memória) ───
    def _loop_jogo(self):
        while self._running and self._conectado:
            estado = self._ler_estado()
            if estado:
                self.after(0, self._atualiza_ui, estado)
                self.after(0, self._set_minha_vez, estado["vez"] == self._meu_id)
            time.sleep(0.1)

    # ─── Atualização de UI ───
    def _atualiza_ui(self, estado: dict):
        if self._ultimo_estado_ui == estado:
            return
        self._ultimo_estado_ui = estado

        if not estado or "vira" not in estado:
            self._log("Aguardando início da rodada pelo servidor...")
            return

        self._lbl_placar.config(text=estado.get("placar", "Esperando..."))
        self._lbl_queda.config(text=f"Queda: {estado.get('queda_atual', 1)}ª")
        self._lbl_valor.config(text=f"Valor: {estado.get('valor_rodada', 1)} pt(s)")

        vira_str = estado.get("vira", "")
        self._vira_widget.set_carta(vira_str)

        self._desenha_mesa(estado.get("mesa", {}))

    def _desenha_mesa(self, mesa: dict):
        for w in self._mesa_frame.winfo_children():
            w.destroy()
        if not mesa:
            tk.Label(self._mesa_frame, text="Mesa vazia — ninguém jogou ainda.",
                     font=FONT_STATUS, fg=TEXT_MUTED, bg=BG_FELT).pack()
            return
        for id_jog, dados in mesa.items():
            col = tk.Frame(self._mesa_frame, bg=BG_FELT, padx=6)
            col.pack(side="left")
            tk.Label(col, text=f"J {id_jog}", font=FONT_STATUS,
                     fg=TEXT_MUTED, bg=BG_FELT).pack()
            enc = dados.get("encoberta", False)
            cw = CartaWidget(col, carta_str=dados.get("carta", "?"),
                             encoberta=enc, pequena=True)
            cw.pack()
            tk.Label(col, text=dados.get("carta", "?"),
                     font=FONT_STATUS, fg=TEXT_LIGHT, bg=BG_FELT).pack()

    def _recebe_cartas(self, dados: str):
        try:
            linha = dados.strip()
            inicio = linha.find("[")
            fim = linha.find("]")
            if inicio != -1 and fim != -1:
                dentro = linha[inicio + 1:fim]
                self._cartas_nomes = [c.strip() for c in dentro.split(",")]
            else:
                self._cartas_nomes = []
        except Exception:
            self._cartas_nomes = []

        self._carta_selecionada = -1
        self._desenha_mao()
        self._log(f"Suas cartas: {self._cartas_nomes}")

    def _desenha_mao(self):
        for w in self._mao_frame.winfo_children():
            w.destroy()
        self._cartas_widgets = []

        for i, nome in enumerate(self._cartas_nomes):
            frame = tk.Frame(self._mao_frame, bg=BG_FELT, padx=4)
            frame.pack(side="left")
            cw = CartaWidget(frame, carta_str=nome,
                             selecionada=(i == self._carta_selecionada))
            cw.pack()
            cw.bind("<Button-1>", lambda e, idx=i: self._seleciona_carta(idx))
            tk.Label(frame, text=nome, font=("Helvetica", 8),
                     fg=TEXT_MUTED, bg=BG_FELT, wraplength=85).pack()
            self._cartas_widgets.append(cw)

    def _seleciona_carta(self, idx: int):
        if not self._minha_vez:
            return
        self._carta_selecionada = idx
        for i, cw in enumerate(self._cartas_widgets):
            cw.set_selecionada(i == idx)
        self._log(f"Carta selecionada: [{idx}] {self._cartas_nomes[idx]}")

    def _set_minha_vez(self, v: bool):
        self._minha_vez = v
        tem_cartas = bool(self._cartas_nomes)
        ativo = v and tem_cartas
        self._set_btns_ativos(ativo)
        if v and tem_cartas:
            self._lbl_status.config(text="🎴 Sua vez! Selecione uma carta e jogue.",
                                     fg=BTN_GREEN)
        elif v and not tem_cartas:
            self._lbl_status.config(text="⏳ Aguardando suas cartas...",
                                     fg=TEXT_MUTED)
        else:
            self._lbl_status.config(text="⏳ Aguardando a jogada do adversário...",
                                     fg=TEXT_MUTED)

    def _set_btns_ativos(self, ativo: bool):
        estado = "normal" if ativo else "disabled"
        for b in (self._btn_jogar, self._btn_coberta, self._btn_truco):
            b.config(state=estado)

    # ─── Ações do jogador ───
    def _remover_carta_local(self, idx: int):
        if 0 <= idx < len(self._cartas_nomes):
            self._cartas_nomes.pop(idx)
            self._carta_selecionada = -1
            self._desenha_mao()

    def _jogar(self):
        if self._carta_selecionada < 0:
            messagebox.showwarning("Selecione uma carta",
                                   "Clique em uma carta antes de jogar.")
            return
        idx = self._carta_selecionada
        self._remover_carta_local(idx)
        self._enviar_comando(f"JOGAR:{idx}")

    def _jogar_coberta(self):
        if self._carta_selecionada < 0:
            messagebox.showwarning("Selecione uma carta",
                                   "Clique em uma carta antes de jogar coberta.")
            return
        idx = self._carta_selecionada
        self._remover_carta_local(idx)
        self._enviar_comando(f"JOGAR:{idx}:COBERTA")

    def _pedir_truco(self):
        self._enviar_comando("TRUCO")

    def _sair(self):
        if messagebox.askyesno("Sair", "Deseja abandonar a partida?"):
            self._enviar_comando("/sair")
            self._on_close()

    def _enviar_comando(self, cmd: str):
        if not self._sock or not self._minha_vez:
            return
        try:
            self._sock.send(cmd.encode())
            self._log(f"▶ Enviado: {cmd}")
            self._set_btns_ativos(False)
            self._minha_vez = False
        except Exception as e:
            self._log(f"✗ Erro ao enviar: {e}")

    # ─── Diálogo de resposta ao Truco ───
    def _mostrar_dialogo_truco(self, valor: int):
        if self._dialogo_truco is not None:
            return
        top = tk.Toplevel(self)
        top.title("Truco!")
        top.geometry("300x150")
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()
        tk.Label(top, text=f"O adversário pediu truco!\nValor: {valor} pontos",
                 font=FONT_BODY, padx=10, pady=10).pack()
        frame = tk.Frame(top)
        frame.pack(pady=10)
        btn_aceitar = tk.Button(frame, text="Aceitar", command=lambda: self._responde_truco(True, top),
                                bg=BTN_GREEN, fg=TEXT_LIGHT, padx=15, pady=5)
        btn_aceitar.pack(side="left", padx=10)
        btn_correr = tk.Button(frame, text="Correr", command=lambda: self._responde_truco(False, top),
                               bg=BTN_RED_BG, fg=TEXT_LIGHT, padx=15, pady=5)
        btn_correr.pack(side="left", padx=10)
        self._dialogo_truco = top

    def _responde_truco(self, aceitou: bool, janela: tk.Toplevel):
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
            
    

    # ─── Leitura da memória compartilhada ───
    def _ler_estado(self) -> dict | None:
        if not self._shared_mem:
            return None
        try:
            dados_brutos = bytes(self._shared_mem.buf[:1024]).decode("utf-8").strip()
            return json.loads(dados_brutos)
        except Exception:
            return None

    # ─── Log ───
    def _log(self, msg: str):
        def _inner():
            self._txt_log.config(state="normal")
            ts = time.strftime("%H:%M:%S")
            self._txt_log.insert("end", f"[{ts}] {msg}\n")
            self._txt_log.see("end")
            self._txt_log.config(state="disabled")
        self.after(0, _inner)

    # ─── Fechamento ───
    def _on_close(self):
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


# ─────────────────────────── Entrypoint ───────────────────────────
if __name__ == "__main__":
    app = TrucoApp()
    app.mainloop()