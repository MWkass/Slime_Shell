import sys
import time
import threading
import itertools
from InquirerPy import inquirer, get_style
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

# Estilo visual personalizado
ESTILO_TUI = get_style({
    "pointer": "ansicyan bold",
    "answer": "ansicyan bold",
    "input": "ansicyan",
    "questionmark": "hidden",
})

# Novo Banner SLIME_SHELL
BANNER = r"""
 ███████╗██╗     ██╗███╗   ███╗███████╗    ███████╗██╗  ██╗███████╗██╗     ██╗     
 ██╔════╝██║     ██║████╗ ████║██╔════╝    ██╔════╝██║  ██║██╔════╝██║     ██║     
 ███████╗██║     ██║██╔████╔██║█████╗      ███████╗███████║█████╗  ██║     ██║     
 ╚════██║██║     ██║██║╚██╔╝██║██╔══╝      ╚════██║██╔══██║██╔══╝  ██║     ██║     
 ███████║███████╗██║██║ ╚═╝ ██║███████╗    ███████║██║  ██║███████╗███████╗███████╗
 ╚══════╝╚══════╝╚═╝╚═╝     ╚═╝╚══════╝    ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝
                               [ SLIME_SHELL SYSTEM ]
"""

def limpar_tela():
    import sys
    sys.stdout.write('\033[2J\033[3J\033[H')
    sys.stdout.flush()

def animar_carregamento(evento: threading.Event, mensagem: str) -> None:
    """Exibe um spinner assíncrono isolado no buffer principal."""
    spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    
    limpar_tela()
    print(f"\033[36m{BANNER}\033[0m")
    
    try:
        while not evento.is_set():
            sys.stdout.write(f"\r{next(spinner)} {mensagem}")
            sys.stdout.flush()
            time.sleep(0.08) # Velocidade ajustada para uma animação mais fluida
    finally:
        sys.stdout.write('\r\033[K')

def exibir_menu_principal():
    limpar_tela()
    print(f"\033[36m{BANNER}\033[0m")
    opcoes = [
        Choice(value="buscar", name="  Buscar Anime Específico"),
        Separator(" "),
        Choice(value="sair", name="  Sair")
    ]
    return inquirer.select(
        message="  Escolha uma opção:",
        choices=opcoes, style=ESTILO_TUI, pointer="❯", qmark="", amark=""
    ).execute()

def exibir_selecao_anime(lista_animes, titulo_menu="Selecione um Anime"):
    limpar_tela()
    print(f"\033[36m{BANNER}\033[0m")
    opcoes = [Separator(" ")]
    for anime in lista_animes:
        nome_exibicao = f"{anime['titulo_exibicao']} (Eps: {anime['ultimo_episodio']})"
        opcoes.append(Choice(value=anime, name=nome_exibicao))
    
    opcoes.extend([Separator(" "), Choice(value="voltar", name="  Voltar")])
    return inquirer.select(
        message=f"  {titulo_menu}:",
        choices=opcoes, style=ESTILO_TUI, pointer="❯", qmark="", amark="", max_height="100%"
    ).execute()

def solicitar_episodio_lista(total_eps):
    limpar_tela()
    print(f"\033[36m{BANNER}\033[0m")
    
    try:
        max_eps = int(total_eps)
    except:
        max_eps = 24 # Fallback
        
    opcoes = [Separator(" ")]
    for i in range(1, max_eps + 1):
        num = str(i).zfill(2)
        opcoes.append(Choice(value=num, name=f"Episódio {num}"))
        
    opcoes.extend([Separator(" "), Choice(value="voltar", name="  Voltar")])
    return inquirer.select(
        message="  Selecione o episódio:",
        choices=opcoes, style=ESTILO_TUI, pointer="❯", qmark="", amark="", max_height="100%"
    ).execute()