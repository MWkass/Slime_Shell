import os
import urllib.parse
import re
import time
import logging
import requests
import atexit
from typing import List, Dict, Any
from .base import AnimeProvider
from functools import lru_cache
from DrissionPage import ChromiumPage, ChromiumOptions

caminho_log = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'debug.log'))
logging.basicConfig(
    filename=caminho_log,
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    filemode='w' 
)

BASE_URL = "https://animesdrive.online"

_navegador_global = None

def iniciar_navegador():
    global _navegador_global
    
    if _navegador_global is not None:
        try:
            _ = _navegador_global.title
            return _navegador_global
        except:
            pass 

    co = ChromiumOptions()
    co.set_browser_path('/usr/bin/brave-browser') 
    
    co.set_argument('--window-size=750,500')
    co.headless(False)
    co.incognito(True)
    co.set_argument('--no-sandbox')
    
    # --- OTIMIZAÇÕES REMOVIDAS (Causavam o Loop do Cloudflare) ---
    # co.set_argument('--disable-gpu') 
    # co.set_argument('--blink-settings=imagesEnabled=false')
    
    # --- MANTEMOS APENAS O QUE É SEGURO ---
    co.set_argument('--log-level=3')
    co.set_argument('--mute-audio')
    co.set_argument('--disable-extensions')
    co.set_argument('--disable-javascript-harmony-shipping')
    
    _navegador_global = ChromiumPage(co)
    
    try:
        _navegador_global.set.window.mini()
    except:
        pass
        
    return _navegador_global

def fechar_navegador_ao_sair():
    global _navegador_global
    if _navegador_global is not None:
        try: _navegador_global.quit()
        except: pass

atexit.register(fechar_navegador_ao_sair)

def esperar_cloudflare(page: ChromiumPage) -> None:
    precisou_captcha = False
    
    while True:
        titulo_aba = page.title.lower()
        
        if any(bloqueio in titulo_aba for bloqueio in ["verificação", "just a moment", "um momento", "cloudflare"]):
            if not precisou_captcha:
                print("\r\033[K  [!] Escudo do Cloudflare detectado! Janela do Brave em foco.")
                try: 
                    page.set.window.normal()
                    time.sleep(0.5)
                except Exception as e: 
                    logging.error(f"Falha ao tentar restaurar janela: {e}")
                precisou_captcha = True
            time.sleep(2)
        else:
            break
            
    if precisou_captcha:
        # print("  [✓] Acesso confirmado! Minimizando novamente...")
        try: 
            page.set.window.mini() 
        except: 
            pass
        time.sleep(2)

def buscar_anime(nome_anime: str) -> list:
    query = nome_anime.strip().replace('-', ' ').replace('_', ' ')
    query = " ".join(query.split())
    url = f"{BASE_URL}/?s={urllib.parse.quote(query)}"
    
    try:
        page = iniciar_navegador()
        logging.info(f"Navegando para a busca: {url}")
        page.get(url)
        
        esperar_cloudflare(page)
        
        if "?s=" not in page.url and "animesdrive" in page.url:
            return []
            
        resultados = []
        artigos = page.eles('css:div.result-item article') or page.eles('css:article.w_item_a')
        
        for artigo in artigos:
            link_tag = artigo.ele('css:a')
            if not link_tag: continue
            
            url_anime = link_tag.link
            if '/anime/' not in url_anime: continue
            
            titulo = ""
            titulo_ele = artigo.ele('css:.title') or artigo.ele('css:h3') or artigo.ele('css:h2')
            if titulo_ele:
                titulo = titulo_ele.text.strip()
            
            if not titulo or titulo.lower() in ['tv', 'ova', 'filme']:
                img_tag = artigo.ele('css:img')
                if img_tag and img_tag.attr('alt'):
                    titulo = img_tag.attr('alt').strip()

            if not titulo or titulo.lower() in ['tv', 'ova', 'filme']:
                titulo = link_tag.attr('title') or link_tag.text.strip()

            if not titulo: continue
            
            idioma = "Dublado" if "dublado" in artigo.html.lower() or "dublado" in titulo.lower() else "Legendado"
            titulo = re.sub(r'(?i)\(dublado\)', '', titulo).strip()
            
            resultados.append({
                "titulo_exibicao": f"{titulo} ({idioma})",
                "url": url_anime,
                "fonte": "AnimesDrive"
            })
            
        return resultados
    except Exception as e:
        logging.error(f"Erro na busca visual: {e}")
        return []

@lru_cache(maxsize=32)
def obter_episodios(url_anime: str) -> list:
    try:
        page = iniciar_navegador()
        
        # GARANTIA DE FOCO: Se o navegador estiver minimizado, o Linux pode pausar o processo.
        # Restauramos para "Acordar" o motor do Brave antes da navegação.
        try: page.set.window.normal()
        except: pass
        
        # LIMPEZA: Para qualquer carregamento anterior que ficou pendente da verificação.
        page.stop_loading() 
        
        # NAVEGAÇÃO FORÇADA: Aumentamos o retry para garantir que ele não desista.
        page.get(url_anime, retry=3, timeout=20)
        
        esperar_cloudflare(page)
        
        episodios = []
        links = page.eles('css:.episodios li a') or page.eles('css:#seasons a')
        
        for a in links:
            href = a.link
            if 'episodio' not in href: continue
            
            match = re.search(r'episodio[s]?[-_]?(\d+)', href, re.IGNORECASE)
            numero = match.group(1) if match else "0"
            
            episodios.append({
                "numero": numero,
                "url": href
            })
            
        episodios.sort(key=lambda x: int(x['numero']) if x['numero'].isdigit() else 0)
        return episodios
    except Exception as e:
        logging.error(f"Erro ao listar episódios: {e}")
        return []

def extrair_links_prioritarios(url_episodio: str) -> dict:
    page = None
    links_encontrados = {} 
    sniffer_ativo = False
    
    logging.info(f"=== INICIANDO EXTRAÇÃO DE VÍDEO BLINDADA ===")
    
    try:
        page = iniciar_navegador()
        
        # Acorda o navegador e limpa o buffer
        try: page.set.window.normal()
        except: pass
        page.stop_loading()
        
        logging.info(f"Acessando página do episódio: {url_episodio}")
        page.get(url_episodio, retry=3, timeout=20)
        
        esperar_cloudflare(page)
        
        seletor_correto = None
        for sel in ['css:.dooplay_player_option', 'css:[data-post][data-nume]']:
            if page.eles(sel): 
                seletor_correto = sel
                break
                
        if not seletor_correto:
            logging.warning("Nenhum botão de servidor encontrado.")
            return {}
            
        embeds_para_vasculhar = []
        quantidade_botoes = len(page.eles(seletor_correto))
        
        for i in range(quantidade_botoes):
            try:
                botoes_atualizados = page.eles(seletor_correto)
                if i >= len(botoes_atualizados): break 

                opcao = botoes_atualizados[i]
                nome_servidor = opcao.text.strip().upper() or f"OPÇÃO {i+1}"
                logging.info(f"Injetando player do servidor: {nome_servidor}...")
                
                opcao.click(by_js=True)
                time.sleep(2) 
                
                iframes = page.eles('css:iframe')
                for iframe in iframes:
                    src = iframe.attr('src')
                    if src and "youtube" not in src:
                        if src not in [e[1] for e in embeds_para_vasculhar]: 
                            embeds_para_vasculhar.append((nome_servidor, src))
                            logging.info(f"[{nome_servidor}] Iframe capturado: {src[:60]}...")
                            break 
            except Exception as e_click:
                logging.error(f"Erro ao clicar no botão {i}: {e_click}")

        if embeds_para_vasculhar:
            logging.info("Ativando Sniffer de Rede...")
            page.listen.start(['.mp4', '.m3u8'])
            sniffer_ativo = True
            
            # --- ACELERAÇÃO: Ordena para atacar o FullHD, FHD e Dublado primeiro ---
            def peso(n):
                n = n.upper()
                if "DUBLADO" in n: return 1 # Dublado agora tem prioridade máxima!
                if "FULLHD" in n or "HLS" in n: return 2
                if "FHD" in n: return 3
                if "HD" in n: return 4
                if "SD" in n: return 5
                return 6
                
            embeds_para_vasculhar.sort(key=lambda x: peso(x[0]))
            
            for nome, embed in embeds_para_vasculhar:
                nome_upper = nome.upper()
                
                # --- 1. BLOQUEIO DO SERVIDOR MOBILE ---
                if "MOBILE" in nome_upper or "CELULAR" in nome_upper:
                    logging.info(f"Ignorando servidor bloqueado: {nome}")
                    continue
                    
                link_final = ""
                
                try:
                    if "jwplayer?source=" in embed:
                        logging.info(f"Descriptografando JWPlayer ({nome})...")
                        match = re.search(r'source=([^&]+)', embed)
                        if match:
                            link_bruto = urllib.parse.unquote(match.group(1))
                            link_final = link_bruto.lstrip('+ ')
                            logging.info(f"[{nome}] JWPlayer decodificado.")

                    elif "http" in embed:
                        logging.info(f"Infiltrando no servidor {nome}...")
                        page.get(embed)
                        time.sleep(0.5) # Pausa mínima só para o HTML chegar na máquina
                        
                        # --- 2. TENTATIVA SUPER SÔNICA: Raio-X no Código-Fonte ---
                        html_pagina = page.html
                        
                        # Escaneia o texto puro buscando variáveis como file:"link", src='link', etc.
                        match = re.search(r'(?:file|src|url|source)\s*[:=]\s*(["\'])(https?://[^\1]+?\.(?:mp4|m3u8)[^\1]*)\1', html_pagina, re.IGNORECASE)
                        if match and "blob:" not in match.group(2):
                            # Limpa possíveis barras invertidas de arquivos JSON (ex: https:\/\/...)
                            link_final = match.group(2).replace('\\/', '/')
                            logging.info(f"[{nome}] Link capturado instantaneamente via Raio-X HTML!")
                            
                        # Se o Raio-X falhar, busca nas tags <video> clássicas
                        if not link_final:
                            video_tag = page.ele('css:video')
                            source_tag = page.ele('css:video source')
                            
                            if video_tag and video_tag.attr('src') and video_tag.attr('src').startswith('http') and "blob" not in video_tag.attr('src'):
                                link_final = video_tag.attr('src')
                            elif source_tag and source_tag.attr('src') and source_tag.attr('src').startswith('http') and "blob" not in source_tag.attr('src'):
                                link_final = source_tag.attr('src')
                        
                        # --- 3. TENTATIVA AGRESSIVA (ÚLTIMO RECURSO): Clique + Sniffer ---
                        if not link_final:
                            logging.info(f"[{nome}] Raio-X falhou. Tentando forçar o Play...")
                            try: 
                                btn_play = page.ele('css:.plyr__control--overlaid, .vjs-big-play-button, .jw-icon-display, .play-button')
                                if btn_play:
                                    btn_play.click()
                                    time.sleep(0.5)
                                    btn_play.click() 
                                else:
                                    corpo = page.ele('css:body')
                                    for _ in range(3):
                                        if corpo: corpo.click()
                                        time.sleep(0.5)
                            except Exception as e_click: pass
                                
                            # Reduzimos o timeout máximo do sniffer de 10 para 5 segundos.
                            # Se o vídeo não carregou em 5s forçando o clique, não vale a pena esperar mais.
                            pacote = page.listen.wait(timeout=5)
                            if pacote:
                                link_final = pacote.url
                                logging.info(f"[{nome}] Pacote interceptado.")
                                
                except Exception as e_sniff:
                    logging.error(f"Erro no sniffer do {nome}: {e_sniff}")

                if link_final:
                    info = obter_info_video(link_final)
                    
                    # Se o site retornou o link, mas o vídeo original foi apagado ou deu timeout
                    if info == "Info Indisponível":
                        nome_unico = f"{nome} [Indisponível]"
                        link_final = "" # Anula o link para garantir que não será clicável
                    else:
                        nome_unico = f"{nome} [{info}]"
                else:
                    # Se o Sniffer não conseguiu extrair nada
                    nome_unico = f"{nome} [Indisponível]"
                    link_final = ""
                    
                contador = 2
                nome_base = nome_unico
                while nome_unico in links_encontrados:
                    nome_unico = f"{nome_base} v{contador}"
                    contador += 1
                    
                # Agora SALVAMOS tudo, mesmo os que falharam (com link vazio)
                links_encontrados[nome_unico] = link_final
            else:
                pass # Removemos o log de warning para não poluir

        return links_encontrados
    except Exception as e:
        logging.critical(f"Erro Fatal na extração: {e}")
        return {}
    finally:
        if page and sniffer_ativo: 
            page.listen.stop()
            
        # --- SOLUÇÃO DO ÁUDIO DUPLO ---
        # Redireciona o navegador fantasma para o vazio. 
        # Isso mata qualquer vídeo rodando e zera o consumo de CPU/RAM.
        if page:
            try: 
                page.get('about:blank')
            except: 
                pass


def obter_info_video(url: str) -> str:
    """Busca o tamanho ou bitrate do vídeo sem fazer o download completo."""
    # Disfarce para o servidor achar que somos um navegador normal
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        if '.m3u8' in url:
            # Aumentado o timeout para 4 segundos
            resp = requests.get(url, headers=headers, timeout=4)
            match = re.findall(r'BANDWIDTH=(\d+)', resp.text)
            if match:
                max_bitrate = max(map(int, match))
                mbps = max_bitrate / 1000000
                return f"~{mbps:.1f} Mbps"
            return "HLS"
            
        else:
            # Aumentado o timeout e usando os headers
            resp = requests.head(url, headers=headers, timeout=4, allow_redirects=True)
            tamanho_bytes = int(resp.headers.get('content-length', 0))
            if tamanho_bytes > 0:
                tamanho_mb = tamanho_bytes / (1024 * 1024)
                return f"{tamanho_mb:.0f} MB"
            return "Tamanho Oculto"
    except Exception as e:
        logging.warning(f"Não foi possível obter info do vídeo: {e}")
        return "Info Indisponível"


class AnimeDrive(AnimeProvider):
    def buscar_anime(self, nome_anime: str) -> List[Dict[str, Any]]:
        return buscar_anime(nome_anime)
        
    def obter_episodios(self, url_anime: str) -> List[Dict[str, Any]]:
        return obter_episodios(url_anime)
        
    def extrair_links(self, url_episodio: str) -> Dict[str, str]:
        return extrair_links_prioritarios(url_episodio)