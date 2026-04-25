# Slime Shell System

O **Slime Shell** é um ecossistema de terminal (TUI) de alto desempenho projetado para a orquestração, busca e reprodução de mídias de forma automatizada. Construído em Python, o sistema utiliza uma arquitetura de bypass de segurança para interagir com servidores de vídeo complexos, superando proteções como Cloudflare e gerando uma experiência de visualização otimizada diretamente no seu terminal.

> **Status do Projeto:** Estável (V1.0)  
> **Tema Visual:** <span style="color: #00FFFF;">Cyan Neon</span>  
> **Arquitetura:** Modular / Baseada em Threads

---

## 📸 Screenshot (Menu Princiapl)

![Menu](https://github.com/MWkass/Slime_Shell/blob/main/menu-principal.png)

---

## 🛠️ Funcionalidades de Elite

* **<span style="color: #00FFFF;">Interface TUI Responsiva:</span>** Navegação fluida com `InquirerPy`, suporte a setas e memória de estado (retoma de onde você parou).
* **<span style="color: #00FFFF;">Motor de Bypass Híbrido:</span>** Utiliza falsificação de TLS e um motor de navegador fantasma (`DrissionPage`) para resolver desafios de segurança em tempo real.
* **<span style="color: #00FFFF;">Injeção de Shaders (Anime4K):</span>** Integração profunda com o `mpv` para aplicar algoritmos de upscaling via hardware (Vulkan/GPU) em tempo real.
* **<span style="color: #00FFFF;">Orquestração Paralela:</span>** Consultas simultâneas em múltiplas fontes com gerenciamento de timeouts e fallbacks automáticos.
* **<span style="color: #00FFFF;">Persistência Inteligente:</span>** Histórico em JSON que monitora progresso de episódios e alerta sobre novos lançamentos nas fontes.

---

## 🚀 Instalação e Execução

Siga rigorosamente os passos abaixo para configurar o ambiente no seu sistema Linux.

### 1. Pré-requisitos do Sistema
O sistema exige ferramentas de processamento de vídeo e um navegador específico para o motor de bypass funcionar corretamente.

```bash
# Atualize o sistema
sudo apt update && sudo apt upgrade -y

# Instale o MPV (Motor de Reprodução)
sudo apt install mpv -y

# Instale o Navegador Brave (Essencial para o bypass via motor fantasma)
sudo apt install curl -y
sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg [https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg](https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg)
echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] [https://brave-browser-apt-release.s3.brave.com/](https://brave-browser-apt-release.s3.brave.com/) stable main"|sudo tee /etc/apt/sources.list.d/brave-browser-release.list
sudo apt update
sudo apt install brave-browser -y
```

### 2. Clonagem e Ambiente Python
Recomenda-se o uso de um ambiente virtual para manter as dependências isoladas.

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/slime-shell.git
cd slime-shell

# Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalação de Dependências Python
Instale as bibliotecas necessárias para a TUI e para o motor de busca:

```bash
pip install -r requirements.txt
```

### 4. Configuração de Shaders (Opcional - Alta Performance)
Para ativar o upscaling **Anime4K** (injetado automaticamente pelo `player.py`), você deve colocar os arquivos `.glsl` na pasta `shaders/` na raiz do projeto.

1. Crie a pasta: `mkdir shaders`

2. Baixe os shaders oficiais do [Anime4K](https://github.com/bloc97/Anime4K/releases).


### 5. Execução
Para iniciar o sistema, basta rodar o script principal:

```bash
python3 main.py
```
---

## 📂 Estrutura do Projeto
. `main.py`: Orquestrador da interface e fluxo principal.

. `api/`: Motores de busca (Animefire, AnimesDrive).

. `utils/`: Utilitários de sistema, persistência de dados e driver do player.

. `shaders/`: Local para arquivos de processamento de imagem GLSL.

---

## ⚡ Otimização de Hardware
O sistema está configurado para utilizar a API Vulkan por padrão para garantir a melhor performance em GPUs modernas. Caso utilize hardware legado, você pode ajustar os parâmetros em `utils/player.py`.
