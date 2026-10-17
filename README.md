# Cena 3D com mesa e objetos — INF1761

Projeto 2 da disciplina de Computação Gráfica (INF1761). A aplicação usa WebGPU e um grafo de cena para representar uma mesa com uma caixa e duas esferas. A cena possui iluminação por fragmento com uma fonte de luz de spot, texturas decal, mapeamento de rugosidade, fog e câmera controlada por arcball.

## Requisitos

- Python 3.10 ou superior;
- uma GPU e drivers gráficos compatíveis com o `wgpu`.

## Instalação

Na raiz do repositório, crie e ative um ambiente virtual.

No Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Execução

Com o ambiente virtual ativo, execute:

```bash
python projeto_2.py
```

Uma janela de 900 × 700 pixels será aberta. Arraste o mouse sobre a janela para girar a visualização com o arcball. Para encerrar, feche a janela.