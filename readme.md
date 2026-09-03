# Curso de Processamento e Visualização de Dados

Navegue nos diretórios acima para acessar os códigos do curso. Para visualizar os slides, utilize os links abaixo:

* M01 - Introdução
    * [Introdução à disciplina](https://chcomin.github.io/curso-processamento-e-visualizacao-de-dados/M01_introducao/1_introducao.html)
    * [Princípios da Gestalt](https://chcomin.github.io/curso-processamento-e-visualizacao-de-dados/M01_introducao/2_principios_gestalt.html)
    * [Formatos de imagens](https://chcomin.github.io/curso-processamento-e-visualizacao-de-dados/M01_introducao/3_formatos_de_imagens.html)
* M02 - Integridade de dados
    * [Formatos de dados](https://chcomin.github.io/curso-processamento-e-visualizacao-de-dados/M02_integridade_de_dados/1_formatos_de_dados.html)
    * [Checagens iniciais](https://chcomin.github.io/curso-processamento-e-visualizacao-de-dados/M02_integridade_de_dados/2_checagens_iniciais.html)
* M03 - Imputação de valores ausentes e transformação de dados
    * [Imputação de valores ausentes](https://chcomin.github.io/curso-processamento-e-visualizacao-de-dados/M03_valores_ausentes_e_transformacoes/1_imputacao_de_valores_ausentes.html)
    * [Escalonamento e transformação](https://chcomin.github.io/curso-processamento-e-visualizacao-de-dados/M03_valores_ausentes_e_transformacoes/2_transformacao_de_dados.html)

## Tópicos abordados

### I. Pré-processamento de Dados

* Identificação e tratamento de valores ausentes, ruídos e *outliers*
* Normalização, padronização e discretização de variáveis contínuas
* Codificação de variáveis categóricas
* Seleção e extração de características
* Seleção e amostragem de instâncias
* Técnicas de reamostragem

### II. Mapeamento e Estética de Visualização

* Mapeamento de dados em atributos estéticos (posição, forma, tamanho, cor)
* Sistemas de coordenadas e eixos
* Tipos de escalas (lineares, logarítmicas, temporais)
* Visualização por Tipo de Dado: Quantidades e proporções, distribuições, relações (X-Y), séries temporais e dados espaciais
* Barras de erro, bandas de confiança e distribuições de probabilidade

### III. Design, Comunicação e Boas Práticas

* Escalas de cores qualitativas, sequenciais e divergentes
* Considerações de acessibilidade e contraste
* Técnicas para lidar com sobreposição de dados
* O que faz um gráfico ser considerado "ruim" (enganoso, ilegível ou desnecessariamente complexo)
* Construção de narrativas visuais

## Preparação do Ambiente

Instalar a IDE [VSCode](https://code.visualstudio.com/), ou usar outra IDE de sua preferência.

Baixar e instalar o gerenciador de ambientes miniconda neste link:

https://www.anaconda.com/docs/getting-started/miniconda/install/linux-install

No terminal, executar os seguintes comandos:

```bash
# Criação do ambiente chamado cursopvd
conda create -n cursopvd python
conda activate cursopvd
conda install -c conda-forge matplotlib numpy pandas scikit-learn notebook
```

Você também pode usar outro gerenciador de ambientes Python. Atualmente o mais popular é o [uv](https://docs.astral.sh/uv/getting-started/installation/). 