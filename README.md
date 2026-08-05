# 🎬 Ontology Movie Recommender

Sistema de recomendação de filmes desenvolvido para a disciplina **SIN-5033**, utilizando uma ontologia OWL/RDF como base semântica e combinando recomendação baseada em conteúdo e filtragem colaborativa.

A aplicação permite cadastrar usuários e filmes, registrar avaliações, explorar o catálogo e gerar recomendações por três métodos diferentes:

- recomendação baseada em conteúdo;
- filtragem colaborativa;
- recomendação híbrida.

A interface foi implementada em **Streamlit**, e os dados são representados e persistidos em **RDF/Turtle**.

---

## Funcionalidades

O sistema permite:

- selecionar usuários cadastrados;
- visualizar suas preferências;
- gerar recomendações por:
  - conteúdo;
  - filtragem colaborativa;
  - método híbrido;
- visualizar os componentes do score de recomendação;
- visualizar afinidades semânticas utilizadas pelo método de conteúdo;
- visualizar usuários semelhantes que influenciaram recomendações colaborativas;
- registrar avaliações de filmes de 1 a 5;
- cadastrar novos usuários;
- cadastrar preferências por gênero, diretor, ator, nacionalidade e idioma;
- cadastrar novos filmes;
- validar regras específicas de filmes e documentários;
- persistir novos dados em RDF;
- explorar o catálogo por:
  - título;
  - gênero;
  - diretor;
  - ator;
  - nacionalidade;
  - idioma.

---

## Ontologia

A ontologia representa os principais conceitos necessários para o domínio de recomendação de filmes.

Entre as classes principais estão:

- `Filme`
- `FilmeDocumentario`
- `Pessoa`
  - `Ator`
  - `Diretor`
  - `Roteirista`
  - `Produtor`
- `Genero`
- `Pais`
- `Idioma`
- `Usuario`
- `Avaliacao`
- `Recomendacao`
- `Premio`
- `Evento`

Algumas das relações modeladas incluem:

```text
Filme --temDiretor--> Diretor
Filme --temAtor--> Ator
Filme --temRoteirista--> Roteirista
Filme --pertenceAoGenero--> Genero

Usuario --prefereGenero--> Genero
Usuario --prefereDiretor--> Diretor
Usuario --prefereAtor--> Ator
Usuario --prefereNacionalidade--> Pais
Usuario --prefereIdioma--> Idioma

Avaliacao --avaliacaoFeitaPor--> Usuario
Avaliacao --avaliaFilme--> Filme
```

A base inicial contém filmes e profissionais reais, incluindo indivíduos como Walter Salles, Fernanda Montenegro, Fernanda Torres, Bong Joon-ho, Hayao Miyazaki, Christopher Nolan e Pedro Almodóvar.

Usuários e avaliações iniciais foram criados como dados sintéticos para permitir a demonstração dos métodos de recomendação.

A consistência lógica da ontologia foi verificada no **Protégé** utilizando o reasoner **HermiT**.

---

## Arquitetura

```text
              OWL / RDF
                  │
                  ▼
     film_recommender_ontology.ttl
                  │
                  │
          + app_data.ttl
                  │
                  ▼
        ontology_service.py
                  │
          ┌───────┴────────┐
          │                │
          ▼                ▼
   recommender.py     validators.py
          │                │
          └───────┬────────┘
                  ▼
               app.py
                  │
                  ▼
              Streamlit
```

### `ontology/film_recommender_ontology.ttl`

Contém a ontologia principal, incluindo:

- classes;
- propriedades;
- axiomas;
- restrições;
- indivíduos da base inicial.

### `ontology/app_data.ttl`

Armazena dados acrescentados pela aplicação, como:

- novos usuários;
- novos filmes;
- novas avaliações;
- preferências cadastradas.

Durante a execução, os dois arquivos são carregados conjuntamente e tratados como um único grafo RDF.

### `src/ontology_service.py`

Responsável por:

- carregar os grafos RDF;
- localizar classes, propriedades e indivíduos;
- extrair filmes, usuários e avaliações;
- cadastrar usuários;
- cadastrar filmes;
- registrar avaliações;
- persistir novos dados em Turtle.

### `src/recommender.py`

Implementa:

- recomendação baseada em conteúdo;
- filtragem colaborativa;
- recomendação híbrida.

### `src/validators.py`

Contém validações operacionais, incluindo:

- nota entre 1 e 5;
- contato obrigatório;
- existência de usuário e filme;
- dados mínimos de cadastro;
- regras de filmes;
- tratamento específico de documentários.

### `app.py`

Implementa a interface da aplicação utilizando Streamlit.

---

## Recomendação baseada em conteúdo

O método compara as preferências declaradas pelo usuário com os metadados semânticos dos filmes.

Os pesos utilizados são:

| Característica | Peso |
|---|---:|
| Gênero | 0,30 |
| Diretor | 0,25 |
| Ator | 0,20 |
| Nacionalidade | 0,15 |
| Idioma | 0,10 |

O score é calculado a partir das características coincidentes.

Exemplo:

```text
Preferências:
Genero = Drama
Diretor = WalterSalles

Filme:
Genero = Drama
Diretor = WalterSalles

Score parcial:
0,30 + 0,25 = 0,55
```

Quando o usuário não declarou uma preferência em determinada categoria, o peso correspondente é removido do denominador. Dessa forma, a ausência de preferência não é interpretada como preferência negativa.

Filmes já avaliados pelo usuário são excluídos das recomendações.

---

## Filtragem colaborativa

A filtragem colaborativa compara usuários com base nos filmes avaliados em comum.

Primeiro é calculada a diferença média absoluta entre suas notas:

```text
diferenca_media =
    media(|nota_usuario_A - nota_usuario_B|)
```

Como as notas variam entre 1 e 5, a diferença máxima possível é 4.

A similaridade básica é:

```text
similaridade_base =
    1 - diferenca_media / 4
```

Também é utilizado um fator de confiança baseado na quantidade de filmes avaliados em comum:

```text
confianca =
    min(numero_filmes_comuns / 3, 1)
```

A similaridade final é:

```text
similaridade =
    similaridade_base * confianca
```

São considerados vizinhos apenas usuários com:

```text
pelo menos 2 filmes em comum
similaridade >= 0,40
```

Para cada filme candidato, o score colaborativo utiliza as notas dos usuários semelhantes ponderadas por sua similaridade.

---

## Recomendação híbrida

O método híbrido combina conteúdo e colaboração:

```text
score_final =
    0,60 * score_conteudo
    + 0,40 * score_colaborativo
```

Quando não existe evidência colaborativa suficiente para determinado filme, o sistema utiliza:

```text
score_final = score_conteudo
```

Esse fallback permite fornecer recomendações mesmo para usuários sem histórico de avaliações, reduzindo o problema de **cold start** por meio das preferências explícitas registradas na ontologia.

---

## Persistência RDF

A ontologia-base é mantida em:

```text
ontology/film_recommender_ontology.ttl
```

Os dados criados pela aplicação são armazenados em:

```text
ontology/app_data.ttl
```

Exemplo conceitual de uma avaliação criada pela aplicação:

```turtle
:Avaliacao_UsuarioAna_PrincesaMononoke
    a owl:NamedIndividual,
      :Avaliacao ;
    :avaliacaoFeitaPor :UsuarioAna ;
    :avaliaFilme :PrincesaMononoke ;
    :notaEstrelas 5 .
```

Essa separação preserva a ontologia principal e permite que a aplicação acrescente novos indivíduos e relações sem reescrever a base original.

---

## Regras e validações

A modelagem utiliza tanto axiomas OWL quanto validações na aplicação.

Entre as regras utilizadas estão:

- todo filme deve possuir pelo menos um gênero;
- todo filme deve possuir pelo menos um diretor;
- filmes não documentários devem possuir pelo menos um ator;
- documentários devem possuir exatamente um diretor e nenhum ator na modelagem adotada;
- avaliações devem ter nota entre 1 e 5;
- todo usuário deve possuir pelo menos um canal de contato.

A distinção entre raciocínio OWL e validação operacional é importante porque OWL utiliza a **Open World Assumption**. A ausência de uma informação não significa necessariamente que ela seja falsa.

Por isso, algumas restrições que precisam impedir imediatamente entradas inválidas são verificadas pela camada Python antes da persistência.

---

## Estrutura do projeto

```text
ontology-movie-recommender/
│
├── ontology/
│   ├── film_recommender_ontology.ttl
│   └── app_data.ttl
│
├── src/
│   ├── __init__.py
│   ├── ontology_service.py
│   ├── recommender.py
│   └── validators.py
│
├── tests/
│   └── test_core.py
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Tecnologias

- Python
- RDFLib
- OWL
- RDF
- Turtle
- Protégé
- HermiT
- Streamlit
- pytest
- Git
- GitHub

---

## Instalação

Clone o repositório e acesse sua pasta:

```bash
git clone <URL_DO_REPOSITORIO>
cd ontology-movie-recommender
```

Crie um ambiente virtual.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Executando a aplicação

Na raiz do projeto:

```bash
streamlit run app.py
```

Por padrão, o Streamlit disponibiliza a aplicação localmente em:

```text
http://localhost:8501
```

---

## Executando os testes

A suíte automatizada pode ser executada com:

```bash
python -m pytest -q
```

Os testes cobrem, entre outros pontos:

- carregamento da ontologia;
- presença dos indivíduos iniciais;
- extração dos metadados RDF;
- geração de identificadores;
- validação de notas;
- validação de contatos;
- regras de filmes e documentários;
- score de recomendação por conteúdo;
- renormalização de preferências ausentes;
- cálculo da similaridade colaborativa.

---

## Inferência

A ontologia permite inferências por meio de sua hierarquia e propriedades semânticas.

Por exemplo:

```text
Diretor SubClassOf Pessoa
```

permite inferir que um indivíduo declarado como `Diretor` também pertence à classe `Pessoa`.

Da mesma forma:

```text
FilmeDocumentario SubClassOf Filme
```

permite inferir que um documentário também é um filme.

A ontologia também possui propriedades inversas e simétricas que permitem derivar novas relações a partir dos fatos declarados.

O reasoner HermiT foi utilizado no Protégé para verificar a consistência lógica da ontologia e calcular inferências.

---

## Limitações

O projeto possui caráter acadêmico e utiliza uma base relativamente pequena de filmes e usuários.

Os metadados dos filmes são representativos e não pretendem registrar integralmente todos os integrantes do elenco, equipe técnica ou todas as características de cada produção.

A filtragem colaborativa utiliza uma métrica simples e interpretável, adequada à escala da demonstração.

Em aplicações maiores poderiam ser exploradas abordagens como:

- correlação de Pearson;
- similaridade por cosseno;
- fatoração de matrizes;
- embeddings;
- métodos de aprendizado de máquina;
- técnicas adicionais de tratamento de cold start.

O objetivo principal do projeto é demonstrar a integração entre **ontologias, representação semântica, RDF/OWL, recomendação e uma aplicação interativa**.

---

## Autor

Projeto desenvolvido por **Renan Rios Diniz** para a disciplina **SIN-5033**.