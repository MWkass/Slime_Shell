import sys
import re
import threading
from ui.menus import limpar_tela, BANNER, animar_carregamento
from InquirerPy import inquirer, get_style
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

from api.animefire import AnimeFire
from api.animedrive import AnimeDrive
from api.orchestrator import buscar_em_todos
from utils.storage import carregar_historico, salvar_historico, remover_historico, salvar_historico_completo
from utils.player import reproduzir_video_mpv
from api.anilist import buscar_anime_por_nome

ESTILO_SLIME = get_style({
    "pointer": "ansicyan bold",
    "answer": "ansicyan bold",
    "input": "ansicyan",
    "questionmark": "hidden",
})

api_fire = AnimeFire()
api_drive = AnimeDrive()

def rodar_com_animacao(funcao, args, mensagem: str):
    evento = threading.Event()
    thread_anim = threading.Thread(target=animar_carregamento, args=(evento, mensagem))
    thread_anim.start()
    try: resultado = funcao(*args)
    finally:
        evento.set()
        thread_anim.join()
        limpar_tela() 
        print(f"\033[36m{BANNER}\033[0m")
    return resultado

def obter_link_final(api_atual, url_ep, versao_preferida=None):
    links_dict = rodar_com_animacao(api_atual.extrair_links, (url_ep,), "[!] Consultando servidores de vídeo...")
    if not links_dict: return None, None
        
    def extrair_peso_qualidade(nome_servidor):
        nome_upper = nome_servidor.upper()
        # Joga os indisponíveis lá para o fundo da lista
        if "INDISPONÍVEL" in nome_upper:
            return -99999.0

        pontuacao = 0.0
        
        # 1. Prioridade de Resolução Base (O motor da ordenação)
        if "FULLHD" in nome_upper or "HLS" in nome_upper: 
            pontuacao += 50000
        elif "FHD" in nome_upper: 
            pontuacao += 30000
        elif "HD" in nome_upper: 
            pontuacao += 10000
            
        # 2. Soma o peso em Megabytes como desempate fino
        match_mb = re.search(r'\[(\d+)\s*MB\]', nome_upper)
        if match_mb:
            pontuacao += float(match_mb.group(1))
            
        # 3. Soma o Bitrate nivelado com os MB
        match_mbps = re.search(r'\[~(\d+(?:\.\d+)?)\s*MBPS\]', nome_upper)
        if match_mbps:
            pontuacao += float(match_mbps.group(1)) * 180
            
        # 4. Desempate Dublado
        if "DUBLADO" in nome_upper:
            pontuacao += 1000
            
        return pontuacao
        
    # Ordena do MAIOR para o MENOR (reverse=True)
    links_ord = sorted(links_dict.items(), key=lambda item: extrair_peso_qualidade(item[0]), reverse=True)
    
    # Ação no topo
    opcoes = [
        Separator("\n  --- [MENU DE SERVIDORES] ---"),
        Choice(value=("cancelar", None), name="[Voltar]"),
        Choice(value=("sair", None), name="[Sair]"),
        Separator(" "),
        Separator("--- [SERVIDORES DISPONÍVEIS] ---")
    ]
    
    for n, l in links_ord:
        if not l or "INDISPONÍVEL" in n.upper():
            opcoes.append(Separator(f"Versão {n}"))
        else:
            opcoes.append(Choice(value=(l, n), name=f"Versão: {n}"))
            
    escolha_link, escolha_nome = inquirer.select(
        message="  Selecione o servidor:", 
        choices=opcoes, 
        pointer="❯", 
        style=ESTILO_SLIME, 
        max_height="70%", 
        qmark="", amark=""
    ).execute()
    
    return escolha_link, escolha_nome

def gerenciar_historico_ui():
    historico = carregar_historico()
    if not historico: return
    
    # MELHORIA DE ORDENAÇÃO: O menu de apagar também ignora as tags!
    historico_ordenado = sorted(historico.keys(), key=lambda k: re.sub(r'\[.*?\]', '', k).strip().lower())
    opcoes = [Separator(" ")] + [Choice(value=t, name=t) for t in historico_ordenado]
    
    try:
        apagar = inquirer.checkbox(message="  [ESPAÇO] Marcar | [ENTER] Confirmar ou Voltar", choices=opcoes, pointer="❯", style=ESTILO_SLIME, max_height="60%", enabled_symbol="✓", disabled_symbol="○", qmark="", amark="").execute()
        if apagar:
            remover_historico(apagar)
            input(f"\n  [✓] {len(apagar)} itens removidos. ENTER para voltar...")
    except KeyboardInterrupt: pass

def menu_episodios(api_atual, titulo_anime, url_anime, ep_inicial=None, tempo_inicial=0, versao_preferida=None):
    eps_brutos = rodar_com_animacao(api_atual.obter_episodios, (url_anime,), "[!] Sincronizando episódios...")
    if not eps_brutos: return

    eps = sorted(eps_brutos, key=lambda x: int(x['numero']) if str(x['numero']).isdigit() else 0)
    
    # Extrator numérico seguro para comparar episódios (ex: saber que 4 < 5)
    def converte_ep(ep_str):
        try: return float(re.search(r'\d+(\.\d+)?', str(ep_str)).group())
        except: return -1.0
    
    ep_auto_play = None 

    while True:
        limpar_tela()
        print(f"\033[36m{BANNER}\033[0m")
        
        if ep_auto_play:
            ep_esc = ep_auto_play
            ep_auto_play = None 
        else:
            titulo_curto = titulo_anime[:55] + "..." if len(titulo_anime) > 55 else titulo_anime
            
            # Ações no topo (Agora com 6 linhas de cabeçalho)
            cabecalho_ep = [
                Separator(f"{titulo_curto}\n"),
                Separator("--- [MENU DE EPISÓDIOS] ---"),
                Choice(value="voltar", name="[Voltar]"),
                Choice(value="sair", name="[Sair]"),
                Separator(" "),
                Separator("--- [LISTA DE EPISÓDIOS] ---")
            ]
            opcoes_ep = cabecalho_ep.copy()
            offset_cabecalho = len(cabecalho_ep) # Conta automaticamente as 6 linhas
            
            default_index = 0
            ep_hist_num = converte_ep(ep_inicial) if ep_inicial else -1.0
            
            for i, e in enumerate(eps):
                ep_atual_num = converte_ep(e['numero'])
                marcador = ""
                
                if ep_inicial and str(e['numero']) == str(ep_inicial):
                    if tempo_inicial == -1:
                        marcador = " [Assistido]"
                        # INTELIGÊNCIA: Se já assistiu, a seta aponta pro PRÓXIMO episódio!
                        default_index = i + 1 if i + 1 < len(eps) else i
                    else:
                        marcador = " [Continuar]"
                        default_index = i # Aponta pra onde parou
                elif ep_hist_num != -1.0 and ep_atual_num != -1.0 and ep_atual_num < ep_hist_num:
                    marcador = " [Assistido]"
                    
                opcoes_ep.append(Choice(value=e, name=f"Episódio {e['numero']}{marcador}"))
                
            # Cálculo blindado contra erros
            index_seguro = default_index + offset_cabecalho
            if index_seguro >= len(opcoes_ep): index_seguro = len(opcoes_ep) - 1

            ep_esc = inquirer.select(
                message=f"  Selecione o Episódio:", 
                choices=opcoes_ep, 
                pointer="❯", 
                style=ESTILO_SLIME,
                # O hasattr garante que nunca mais dará o erro do Separator!
                default=opcoes_ep[index_seguro].value if hasattr(opcoes_ep[index_seguro], 'value') else None,
                max_height="70%", 
                qmark="", amark=""
            ).execute()

        if ep_esc == "voltar": return
        if ep_esc == "sair":
            limpar_tela()
            sys.exit(0)

        lnk, versao_escolhida = obter_link_final(api_atual, ep_esc['url'], versao_preferida)
        if not lnk or lnk == "cancelar": continue
        if not lnk or lnk == "sair":
            limpar_tela()
            sys.exit(0)
        
        versao_preferida = versao_escolhida
        
        # --- CORREÇÃO 1: O "Carimbo" (Referer) do Animefire ---
        mascara = "https://animesdrive.online" if api_atual == api_drive else "https://animefire.io/"
        tempo_uso = tempo_inicial if (ep_inicial and str(ep_esc['numero']) == str(ep_inicial) and tempo_inicial != -1) else 0
        
        novo_t, finalizou, sucesso = reproduzir_video_mpv(lnk, f"{titulo_anime} - Ep {ep_esc['numero']}", referer=mascara, tempo_inicial=tempo_uso)
        
        if sucesso:
            # Lógica original de progresso...
            if finalizou:
                salvar_historico(titulo_anime, url_anime, ep_esc['numero'], -1, versao_preferida)
                ep_inicial, tempo_inicial = ep_esc['numero'], -1
            else:
                salvar_historico(titulo_anime, url_anime, ep_esc['numero'], novo_t, versao_preferida)
                ep_inicial, tempo_inicial = ep_esc['numero'], novo_t
        else:
            # MELHORIA D: Lógica de Fallback
            outra_api_nome = "AnimesDrive" if api_atual == api_fire else "Animefire"
            print(f"\n  \033[31m[!] Erro de Reprodução:\033[0m O servidor da fonte atual falhou ou negou a conexão.")
            
            tentar_fallback = inquirer.confirm(
                message=f"  Deseja tentar encontrar este episódio no {outra_api_nome}?",
                default=True
            ).execute()
            
            if tentar_fallback:
                # Limpa o título para uma busca limpa
                termo_fb = re.sub(r'\[.*?\]|\(.*?\)', '', titulo_anime).strip()
                res_fb = buscar_em_todos(termo_fb)
                
                # Procura o mirror na outra fonte
                alvo = next((a for a in res_fb if a['fonte_api'] != ("fire" if api_atual == api_fire else "drive")), None)
                
                if alvo:
                    api_fb = api_drive if api_atual == api_fire else api_fire
                    return menu_episodios(api_fb, alvo['titulo_exibicao'], alvo['url'], ep_inicial=ep_esc['numero'], versao_preferida=None)
                else:
                    print(f"  [!] Infelizmente não encontramos mirrors para este anime no {outra_api_nome}.")
                    input("  Pressione ENTER para voltar aos servidores...")
                    
                    # --- CORREÇÃO 2: Volta para a lista de servidores ---
                    ep_auto_play = ep_esc 
                    versao_preferida = None # Limpa a auto-seleção para não dar loop
                    continue
            else:
                # --- CORREÇÃO 2: Se disser "NÃO", volta para a lista de servidores ---
                ep_auto_play = ep_esc 
                versao_preferida = None 
                continue

        limpar_tela()
        print(f"\033[36m{BANNER}\033[0m")
        idx = eps.index(ep_esc)
        
        titulo_curto = titulo_anime[:55] + "..." if len(titulo_anime) > 55 else titulo_anime
        opcoes_pos = [
            Separator(f"{titulo_curto}"),
            Separator(f"[Episódio {ep_esc['numero']} Concluído]"),
            Separator(" ")
        ]
        
        if idx < len(eps) - 1:
            opcoes_pos.append(Choice(value="prox", name="Próximo Episódio"))
        if idx > 0:
            opcoes_pos.append(Choice(value="ant", name="Episódio Anterior"))
        opcoes_pos.append(Choice(value="lista", name="Voltar"))
        opcoes_pos.append(Choice(value="sair", name="Sair"))

        acao = inquirer.select(
            message=f"  O que deseja fazer agora?",
            choices=opcoes_pos,
            pointer="❯",
            style=ESTILO_SLIME,
            max_height="60%",
            qmark="", amark=""
        ).execute()

        if acao == "prox":
            ep_auto_play = eps[idx + 1]
        elif acao == "ant":
            ep_auto_play = eps[idx - 1]
        elif acao == "sair":
            limpar_tela()
            sys.exit(0)

def main():
    while True:
        limpar_tela()
        print(f"\033[36m{BANNER}\033[0m")
        historico = carregar_historico()
        
        # 1. Botões de ação sempre no topo!
        opcoes = [
            Choice(value={"acao": "buscar"}, name="[Buscar Anime]"),
            Choice(value={"acao": "verificar_atualizacoes"}, name="[Verificar Novos Episódios]"),
            Choice(value={"acao": "gerenciar_historico"}, name="[Gerenciar Histórico]"),
            Choice(value={"acao": "sair"}, name="[Sair]")
        ]
        
        # 2. Histórico vem embaixo
        if historico:
            opcoes.extend([Separator(" "), Separator("--- [SEU HISTÓRICO] ---")])
            # MELHORIA: Ordena alfabeticamente ignorando tags como [Animefire] e [AnimesDrive]
            historico_ordenado = sorted(historico.items(), key=lambda item: re.sub(r'\[.*?\]', '', item[0]).strip().lower())
            
            for t, d in historico_ordenado:
                t_val = d.get('tempo', 0)
                if t_val == -1: tempo_str = "Assistido"
                elif t_val > 0: tempo_str = f"{t_val // 60:02d}:{t_val % 60:02d}"
                else: tempo_str = "Início"
                
                t_curto = t[:45] + "..." if len(t) > 45 else t
                tag_novo = " [Novo Episodio]" if d.get('novo_ep') else ""

                opcoes.append(Choice(value={"acao": "continuar", "titulo": t, "url": d['fonte'], "ep": d['episodio'], "tempo": t_val, "versao": d.get('versao')}, name=f". {t_curto} (Ep {d['episodio']}) - [{tempo_str}]{tag_novo}"))        
        
        # Travamos o max_height em 70% para nunca "vazar" do terminal
        esc = inquirer.select(message="  --- [MENU PRINCIPAL] --- ", choices=opcoes, pointer="❯", style=ESTILO_SLIME, max_height="70%", qmark="", amark="").execute()

        if esc["acao"] == "sair":
            limpar_tela()
            sys.exit(0)

        elif esc["acao"] == "gerenciar_historico": gerenciar_historico_ui()
        elif esc["acao"] == "continuar":
            api_at = api_fire if "animefire" in esc["url"] else api_drive
            # AQUI: Adicionamos o versao_preferida no final
            menu_episodios(api_at, esc['titulo'], esc['url'], ep_inicial=esc['ep'], tempo_inicial=esc['tempo'], versao_preferida=esc.get('versao'))
        
        elif esc["acao"] == "verificar_atualizacoes":
            def checar_atualizacoes():
                hist = carregar_historico()
                if not hist: return 0
                
                import time
                atualizados = 0
                for titulo, dados in hist.items():
                    url = dados.get('fonte')
                    if not url: continue
                    
                    try:
                        def converte_ep(ep_str):
                            try: return float(re.search(r'\d+(\.\d+)?', str(ep_str)).group())
                            except: return -1.0
                            
                        # A MÁGICA: Consultamos a fonte real (Animefire ou Drive) 
                        # em vez de depender de APIs terceiras como a AniList!
                        api_at = api_fire if "animefire" in url else api_drive
                        eps_site = api_at.obter_episodios(url)
                        
                        if not eps_site: continue
                        
                        # Pega o maior número de episódio que está no site agora
                        max_ep_site = max([converte_ep(e['numero']) for e in eps_site])
                        ep_visto = converte_ep(dados.get('episodio', -1))
                        
                        # Se o site fez upload de um episódio maior que o seu, marca como novo!
                        if max_ep_site > ep_visto:
                            hist[titulo]['novo_ep'] = True
                            atualizados += 1
                            
                        time.sleep(1) # Pausa educada para não dar spam nos sites
                    except Exception: 
                        pass
                
                salvar_historico_completo(hist)
                return atualizados
                
            qtd = rodar_com_animacao(checar_atualizacoes, (), "[!] Checando novidades direto nas fontes (Pode demorar)...")
            input(f"\n  [✓] Verificação concluída! {qtd} animes com novos episódios.\n  Pressione ENTER para voltar...")
            
        elif esc["acao"] == "buscar":
            while True:
                limpar_tela()
                print(f"\033[36m{BANNER}\033[0m")
                
                termo = inquirer.text(message="  Digite o nome do anime:\n  >", style=ESTILO_SLIME, qmark="", amark="").execute()
                if not termo.strip(): break

                animes = rodar_com_animacao(buscar_em_todos, (termo,), f"[!] Consultando todas as fontes...")
                if not animes:
                    input("\n  [!] Nenhum anime encontrado. Pressione ENTER para tentar novamente...")
                    continue
                
                # MELHORIA DE ORDENAÇÃO: Agrupa ignorando a tag [Animefire] / [AnimesDrive]. 
                # Agora o mesmo anime das duas fontes ficam um em cima do outro na lista!
                animes = sorted(animes, key=lambda a: re.sub(r'\[.*?\]', '', a['titulo_exibicao']).strip().lower())
                
                while True:
                    limpar_tela()
                    print(f"\033[36m{BANNER}\033[0m")
                    
                    # Ações no topo
                    opcoes_an = [
                        Separator("\n  --- [MENU DE BUSCA] ---"),
                        Choice(value="voltar", name="[Voltar]"), 
                        Choice(value="sair", name="[Sair]"),
                        Separator(" "),
                        Separator("--- [RESULTADOS DA BUSCA] ---")
                    ]
                    
                    # Lista de resultados embaixo
                    for a in animes:
                        opcoes_an.append(Choice(value=a, name=a['titulo_exibicao']))
                    
                    an_esc = inquirer.select(message="  Selecione o Anime:", choices=opcoes_an, pointer="❯", style=ESTILO_SLIME, max_height="70%", qmark="", amark="").execute()
                    
                    if an_esc == "voltar": break
                    if an_esc == "sair":
                        limpar_tela()
                        sys.exit(0)

                    api_selecionada = api_fire if an_esc["fonte_api"] == "fire" else api_drive
                    menu_episodios(api_selecionada, an_esc['titulo_exibicao'], an_esc['url'])

if __name__ == "__main__":
    main()