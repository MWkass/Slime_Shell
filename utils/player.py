import os
import re
import subprocess

# Resolve o diretório raiz do projeto (uma pasta acima de utils/)
CAMINHO_ATUAL = os.path.abspath(os.path.dirname(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(CAMINHO_ATUAL, '..'))

def reproduzir_video_mpv(url_video: str, titulo: str, referer: str = None, tempo_inicial: int = 0):
    print(f"\n  [!] Link de vídeo obtido! Preparando Injeções do MPV...")
    pasta_shaders = os.path.join(DIRETORIO_RAIZ, 'shaders')
    shader_args = []
    
    if os.path.exists(pasta_shaders):
        arquivos_glsl = os.listdir(pasta_shaders)
        shaders_selecionados = []
        
        for prefixo in ['restore_cnn', 'darken', 'upscale_cnn_x2']:
            for sufixo in ['_vl.glsl', '_l.glsl', '_m.glsl', '_s.glsl', 'hq.glsl', '.glsl']:
                encontrado = [f for f in arquivos_glsl if prefixo in f.lower() and f.lower().endswith(sufixo)]
                if encontrado:
                    shaders_selecionados.append(os.path.join(pasta_shaders, encontrado[0]))
                    break 
                    
        if shaders_selecionados:
            shader_args = [f"--glsl-shaders={':'.join(shaders_selecionados)}"]
            print(f"  [!] Anime4K Ativado ({len(shaders_selecionados)} shaders injetados).")
            
    arquivo_capitulos = os.path.join(DIRETORIO_RAIZ, 'temp_chapters.txt')
    with open(arquivo_capitulos, 'w', encoding='utf-8') as f:
        f.write("CHAPTER01=00:00:00.000\nCHAPTER01NAME=Início\nCHAPTER02=00:01:30.000\nCHAPTER02NAME=Pós-Abertura (P)\n")
        
    arquivo_teclas = os.path.join(DIRETORIO_RAIZ, 'temp_input.conf')
    with open(arquivo_teclas, 'w', encoding='utf-8') as f:
        f.write("p seek 90 exact\n")
        
    comando_mpv = ["mpv", url_video, "--fs", f"--force-media-title={titulo}", "--cache=yes", "--demuxer-max-bytes=400M", "--cache-pause=no", "--vo=gpu-next", "--gpu-api=vulkan", "--hwdec=auto-safe", "--profile=gpu-hq", f"--chapters-file={arquivo_capitulos}", f"--input-conf={arquivo_teclas}"]    
    
    if referer: comando_mpv.append(f"--http-header-fields=Referer: {referer}")
    if tempo_inicial > 0: comando_mpv.append(f"--start={tempo_inicial}")

    mpv_cinema_configs = [
        "--saturation=18",        
        "--contrast=6",           
        "--gamma=-2",             
        "--deband=yes", "--deband-iterations=2", "--deband-threshold=35", "--deband-range=16", "--deband-grain=5",
        "--scale=ewa_lanczossharp", "--cscale=ewa_lanczossoft", 
        "--sigmoid-upscaling=yes", 
        "--video-sync=display-resample", "--interpolation=yes", "--tscale=oversample"
    ]
    
    comando_mpv.extend(shader_args + mpv_cinema_configs)
    
    processo = subprocess.Popen(comando_mpv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True)
    tempo_parado, tempo_total = 0, 0
    for linha in processo.stdout:
        match = re.search(r'[AVV]:\s*(\d{2}):(\d{2}):(\d{2})\s*/\s*(\d{2}):(\d{2}):(\d{2})', linha)
        if match:
            h, m, s, h_tot, m_tot, s_tot = match.groups()
            tempo_parado = int(h) * 3600 + int(m) * 60 + int(s)
            tempo_total = int(h_tot) * 3600 + int(m_tot) * 60 + int(s_tot)
    processo.wait()
    # Final da função reproduzir_video_mpv
    for f in [arquivo_capitulos, arquivo_teclas]:
        if os.path.exists(f): os.remove(f)
        
    falta = tempo_total - tempo_parado
    finalizou = True if (tempo_total > 0 and falta <= 90) else False
    
    # NOVA LÓGICA: Verifica se o vídeo tocou por pelo menos 1 segundo
    sucesso_reproducao = tempo_total > 0 
    
    # Retornamos 3 variáveis agora
    return tempo_parado, finalizou, sucesso_reproducao