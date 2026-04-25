import cloudscraper
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
from functools import lru_cache
from .base import AnimeProvider

BASE_URL = "https://animefire.io"

def obter_scraper_seguro():
    """Gera um cliente de rede camuflado para burlar o Cloudflare."""
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )

def smart_get(url, scraper):
    """Tenta baixar o HTML via scraper; se falhar, usa o navegador (Plano B)."""
    try:
        resposta = scraper.get(url, timeout=15)
        resposta.raise_for_status()
        return resposta.text
    except Exception:
        print(f"  [!] Cloudflare ou erro de rede detectado. Ativando Plano B (Navegador)...")
        from api.animedrive import iniciar_navegador # Import local para evitar importação circular
        page = iniciar_navegador()
        page.get(url)
        # Espera um pouco para garantir que scripts de proteção rodem
        time.sleep(2) 
        return page.html

def buscar_anime(nome_anime: str) -> list:
    """Busca o anime e retorna os resultados limpos."""
    busca_formatada = nome_anime.replace(' ', '-').lower()
    url = f"{BASE_URL}/pesquisar/{busca_formatada}"
    
    try:
        scraper = obter_scraper_seguro()
        resposta = scraper.get(url, timeout=15)
        resposta.raise_for_status()
        html_puro = resposta.text
    except Exception as e:
        print(f"  [!] Cloudflare bloqueou o Animefire. Ativando Plano B (Navegador)...")
        from api.animedrive import iniciar_navegador # Importação local de emergência
        page = iniciar_navegador()
        page.get(url)
        html_puro = page.html
        
    try:
        soup = BeautifulSoup(html_puro, 'html.parser')
        resultados = []
        caixas_animes = soup.find_all('div', class_='divCardUltimosEps')
        
        for caixa in caixas_animes:
            tag_link = caixa.find('a')
            if tag_link:
                titulo_bruto = tag_link.text.strip()
                link = tag_link['href']
                
                if titulo_bruto and link:
                    titulo_limpo = re.sub(r'\s+\d+\.\d+\s+[A-Z\d]+$', '', titulo_bruto).strip()
                    titulo_limpo = titulo_limpo.replace('\xa0', ' ')
                    
                    if "(Dublado)" in titulo_limpo:
                        idioma = "Dublado"
                        titulo_limpo = titulo_limpo.replace("(Dublado)", "").strip()
                    else:
                        idioma = "Legendado"

                    resultados.append({
                        "titulo_exibicao": f"{titulo_limpo} ({idioma})",
                        "url": link,
                        "ultimo_episodio": "?"
                    })
        return resultados
    except Exception as e:
        print(f"  [!] Erro fatal ao buscar animes no Animefire: {e}")
        return []

@lru_cache(maxsize=32)
def obter_episodios(url_anime: str) -> list:
    """Entra na página do anime e extrai a lista de episódios com suporte a Plano B."""
    scraper = obter_scraper_seguro()
    html_puro = smart_get(url_anime, scraper)
    
    try:
        soup = BeautifulSoup(html_puro, 'html.parser')
        episodios = []
        urls_vistas = set()
        
        slug_anime = url_anime.split('/')[-1].replace('-todos-os-episodios', '')
        links = soup.find_all('a', href=True)
        
        for a in links:
            href = a['href']
            if f"/animes/{slug_anime}/" in href:
                numero_ep = href.split('/')[-1]
                if href not in urls_vistas:
                    urls_vistas.add(href)
                    episodios.append({
                        "numero": numero_ep,
                        "url": href
                    })
                    
        episodios.reverse() # Garante ordem crescente
        return episodios
    except Exception as e:
        print(f"  [!] Erro ao extrair episódios no Animefire: {e}")
        return []

def extrair_link_video(url_episodio: str) -> str:
    """Extrai o link direto (.mp4) com redundância de acesso."""
    scraper = obter_scraper_seguro()
    html_puro = smart_get(url_episodio, scraper)
    
    try:
        soup = BeautifulSoup(html_puro, 'html.parser')
        video_tag = soup.find('video')
        
        if not video_tag or 'data-video-src' not in video_tag.attrs:
            return ""
            
        url_api_json = video_tag['data-video-src']
        
        # Segunda camada de proteção para a API de JSON
        try:
            resposta_api = scraper.get(url_api_json, timeout=15)
            dados_video = resposta_api.json()
        except Exception:
            # Se a API de JSON for bloqueada, tentamos acessá-la via navegador
            from api.animedrive import iniciar_navegador
            page = iniciar_navegador()
            page.get(url_api_json)
            # O DrissionPage pode retornar o JSON como texto puro na página
            import json
            dados_video = json.loads(page.ele('css:body').text)
        
        link_direto = None
        for qualidade in dados_video.get('data', []):
            link_direto = qualidade.get('src')
            
        return link_direto if link_direto else ""
    except Exception as e:
        print(f"  [!] Falha na API de vídeo do Animefire: {e}")
        return ""

class AnimeFire(AnimeProvider):
    def buscar_anime(self, nome_anime: str) -> List[Dict[str, Any]]:
        return buscar_anime(nome_anime)
        
    def obter_episodios(self, url_anime: str) -> List[Dict[str, Any]]:
        return obter_episodios(url_anime)
        
    def extrair_links(self, url_episodio: str) -> Dict[str, str]:
        link = extrair_link_video(url_episodio)
        return {"Servidor Nativo": link} if link else {}