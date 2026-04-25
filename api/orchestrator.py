import concurrent.futures
import datetime
from typing import List, Dict, Any
from .animefire import AnimeFire
from .animedrive import AnimeDrive
from utils.storage import carregar_cache_buscas, salvar_no_cache_buscas

def buscar_em_todos(termo: str, timeout: int = 25) -> List[Dict[str, Any]]:
    termo_limpo = termo.strip().lower()
    
    # Tenta ler do Cache primeiro
    cache = carregar_cache_buscas()
    if termo_limpo in cache:
        data_cache = datetime.datetime.strptime(cache[termo_limpo]['data'], "%Y-%m-%d %H:%M:%S")
        # Se a busca foi feita há menos de 24h, retorna o cache
        if (datetime.datetime.now() - data_cache).days < 1:
            return cache[termo_limpo]['resultados']

    # Se não houver cache, faz a busca normal
    api_fire = AnimeFire()
    api_drive = AnimeDrive()
    resultados = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futuro_fire = executor.submit(api_fire.buscar_anime, termo)
        futuro_drive = executor.submit(api_drive.buscar_anime, termo)
        
        # Coletando resultados com Timeout Seguro
        try:
            rf = futuro_fire.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print("\r\033[K  [!] Timeout: O servidor do Animefire demorou muito a responder.")
            rf = []
        except Exception as e:
            print(f"\r\033[K  [!] Falha no Animefire: {e}")
            rf = []
            
        try:
            rd = futuro_drive.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print("\r\033[K  [!] Timeout: O servidor do AnimesDrive demorou muito a responder.")
            rd = []
        except Exception as e:
            print(f"\r\033[K  [!] Falha no AnimesDrive: {e}")
            rd = []

    # Agrupamento de resultados (código original)
    for a in rf: 
        a.update({"titulo_exibicao": f"[Animefire] {a['titulo_exibicao']}", "fonte_api": "fire"})
        resultados.append(a)
    for a in rd: 
        a.update({"titulo_exibicao": f"[AnimesDrive] {a['titulo_exibicao']}", "fonte_api": "drive"})
        resultados.append(a)
        
    # Salva no Cache para a próxima vez
    if resultados:
        salvar_no_cache_buscas(termo_limpo, resultados)
        
    return resultados