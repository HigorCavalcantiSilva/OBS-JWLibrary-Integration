# OBS Auto Scene Switcher com OCR

Este projeto monitora uma pasta específica (`JWLibrary/.SecondDisplay`) e, com base em arquivos criados ou removidos e na leitura de texto via OCR na tela, alterna automaticamente cenas no OBS Studio.

Ele detecta se um vídeo está ativo ou se o texto na tela contém um determinado ano (`TEXT_YEAR`) e muda para a cena correspondente: câmera ou monitor.

---

## Funcionalidades

### Monitoramento de arquivos
- Verifica se há arquivos `_true` na pasta configurada para identificar se um vídeo está ativo.

### OCR Inteligente
- Captura a tela e detecta texto específico para alternar cenas automaticamente.

### Integração com OBS WebSocket
- Muda cenas automaticamente conforme a detecção de vídeo ou texto.

### Multithread
- OCR e monitoramento de arquivos rodam em paralelo para maior desempenho.

---

## Configuração

### 1. Instale o Python
- Recomendado: **Python 3.11 ou superior**

### 2. Clone o projeto
```
git clone <URL_DO_REPOSITORIO>
cd <PASTA_DO_PROJETO>
```

### 3. Crie o arquivo `.env`
Na raiz do projeto, crie um arquivo `.env` com as seguintes variáveis:
```
OBS_URL=localhost
OBS_PORT=4444
OBS_PASSWORD=senha_do_obs
TEXT_YEAR=Mateus 5:3
SCT_MONITOR_INDEX=2
TIME_SLEEP_VERIFICATION=1
SCENE_CAMERA=Camera
SCENE_MONITOR=Monitor
```
> ⚠️ Certifique-se de que o `.env` esteja sempre na mesma pasta do script ou do `.exe`.

### 4. Instale o Tesseract OCR
- Baixe e instale o Tesseract OCR: [https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)
- Adicione o caminho do Tesseract ao PATH do sistema, se necessário.

### 5. Instale as dependências Python
```
pip install -r requirements.txt
```

---

## Uso

Execute o script normalmente:
```
python main.py
```

O programa irá:
1. Conectar ao OBS Studio via WebSocket
2. Monitorar a pasta `JWLibrary/.SecondDisplay`
3. Rodar OCR no monitor configurado
4. Alternar cenas automaticamente entre câmera e monitor

> Dica: Antes da primeira execução, crie a pasta `JWLibrary/.SecondDisplay` se ela não existir, para evitar erros.

---

## Build para EXE

Para gerar um executável Windows, use o **PyInstaller** com o comando:
```
pyinstaller --noconsole --onefile --collect-all pytesseract --collect-all mss --collect-all numpy --collect-all cv2 --collect-all PIL --hidden-import=cv2 --hidden-import=PIL main.py
```

- O executável será gerado na pasta `dist/main.exe`
- ⚠️ O `.env` deve estar na mesma pasta do `.exe` após a compilação.

---

## Estrutura de Pastas
```
.
├── main.py
├── requirements.txt
├── .env
└── README.md
```

---

## Requisitos

- Python 3.11+
- OBS Studio com WebSocket ativo
- Tesseract OCR instalado
- Monitor configurado corretamente (`SCT_MONITOR_INDEX`)

---

## requirements.txt
```
opencv-python
numpy
pytesseract
mss
obs-websocket-py
python-dotenv
watchdog
Pillow
```

---

## Dicas Extras

- Sempre teste primeiro com Python antes de gerar o `.exe`
- Para evitar que o OCR leia partes indesejadas, ajuste a função `extract_text_region` no script se necessário
- Se houver problemas de conexão com OBS, verifique URL, porta e senha no `.env