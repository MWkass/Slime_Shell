# Slime Shell System

O **Slime Shell** é um ecossistema de terminal (TUI) de alto desempenho projetado para a orquestração, busca e reprodução de mídias de forma automatizada. Construído em Python, o sistema utiliza uma arquitetura de bypass de segurança para interagir com servidores de vídeo complexos, superando proteções como Cloudflare e gerando uma experiência de visualização otimizada diretamente no seu terminal.

> **Status do Projeto:** Estável (V1.0)  
> **Tema Visual:** <span style="color: #00FFFF;">Cyan Neon</span>  
> **Arquitetura:** Modular / Baseada em Threads

---

## 📸 Screenshots (Preview)

Aqui você pode adicionar as capturas de tela para mostrar a interface em ação (basta substituir os links pelas imagens reais do seu projeto):

| Menu Principal | Busca de Animes | Reprodução via MPV |
| :--- | :--- | :--- |
| ![Menu](https://via.placeholder.com/400x225/000000/00FFFF?text=Screenshot+Menu+Principal) | ![Busca](https://via.placeholder.com/400x225/000000/00FFFF?text=Screenshot+Busca) | ![Player](https://via.placeholder.com/400x225/000000/00FFFF?text=Screenshot+MPV+Player) |

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
