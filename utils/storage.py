import json
import os
import sys
import datetime
from typing import Dict, Any

# Força a leitura do caminho absoluto a partir deste arquivo (que está na pasta utils/)
CAMINHO_ATUAL = os.path.abspath(os.path.dirname(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(CAMINHO_ATUAL, '..'))

ARQUIVO_HISTORICO = os.path.join(DIRETORIO_RAIZ, "historico.json")
ARQUIVO_LOG = os.path.join(DIRETORIO_RAIZ, "debug.log")
ARQUIVO_CONFIG = os.path.join(DIRETORIO_RAIZ, "config.json")

ARQUIVO_CACHE = os.path.join(DIRETORIO_RAIZ, "cache_buscas.json")

def carregar_cache_buscas() -> Dict[str, Any]:
    if not os.path.exists(ARQUIVO_CACHE): return {}
    try:
        with open(ARQUIVO_CACHE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def salvar_no_cache_buscas(termo: str, resultados: list):
    cache = carregar_cache_buscas()
    cache[termo.lower()] = {
        "resultados": resultados,
        "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(ARQUIVO_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception as e:
        registrar_log(f"Erro ao salvar cache de busca: {e}")

def registrar_log(mensagem: str):
    """Grava eventos e erros com data e hora no arquivo debug.log."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    texto = f"[{timestamp}] {mensagem}\n"
    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
            f.write(texto)
    except Exception as e:
        print(f"  [AVISO] Não foi possível criar o log em: {ARQUIVO_LOG}")

def carregar_historico() -> Dict[str, Any]:
    if not os.path.exists(ARQUIVO_HISTORICO): return {}
    try:
        with open(ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def salvar_historico(titulo_anime: str, fonte: str, index_episodio: int, tempo_segundos: int = 0, versao: str = "") -> None:
    historico = carregar_historico()
    
    anime_data = historico.get(titulo_anime, {})
    anime_data.update({
        "episodio": index_episodio, 
        "fonte": fonte,
        "tempo": tempo_segundos,
        "versao": versao
    })
    
    # Remove a flag de novo episódio pois o usuário acabou de atualizar seu progresso
    if "novo_ep" in anime_data:
        del anime_data["novo_ep"]
        
    historico[titulo_anime] = anime_data
    try:
        with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
            json.dump(historico, f, indent=4, ensure_ascii=False)
    except Exception as e:
        registrar_log(f"Erro ao salvar histórico: {e}")

def salvar_historico_completo(historico_atualizado: Dict[str, Any]) -> None:
    try:
        with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
            json.dump(historico_atualizado, f, indent=4, ensure_ascii=False)
    except Exception as e:
        registrar_log(f"Erro ao salvar histórico em lote: {e}")

def remover_historico(titulos_para_remover: list) -> None:
    """Remove uma lista de animes do histórico permanentemente."""
    historico = carregar_historico()
    mudou = False
    for titulo in titulos_para_remover:
        if titulo in historico:
            del historico[titulo]
            mudou = True
            
    if mudou:
        try:
            with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

def limpar_historico() -> None:
    """Apaga todos os registros do histórico de reprodução."""
    try:
        with open(ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def gerenciar_tamanho_log() -> None:
    """Rotaciona o debug.log caso ele ultrapasse 2MB de tamanho."""
    limite_mb = 2 * 1024 * 1024 
    try:
        if os.path.exists(ARQUIVO_LOG) and os.path.getsize(ARQUIVO_LOG) > limite_mb:
            with open(ARQUIVO_LOG, 'w', encoding='utf-8') as f:
                f.write("[ SISTEMA ] Arquivo de log rotacionado automaticamente (Excedeu 2MB).\n")
    except Exception:
        pass

def carregar_config() -> Dict[str, Any]:
    if not os.path.exists(ARQUIVO_CONFIG): return {}
    try:
        with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def salvar_config(chave: str, valor: Any) -> None:
    config = carregar_config()
    config[chave] = valor
    try:
        with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception:
        pass