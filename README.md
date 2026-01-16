# Lycosidae Interpreter API

O **Lycosidae Interpreter** é o componente central de persistência e abstração de dados da plataforma Lycosidae CTF. Ele atua como uma camada intermediária entre o **Backend (Gateway)** e o banco de dados **MariaDB**, garantindo que toda a lógica de acesso a dados seja centralizada e segura.

Esta API foi desenhada para ser resiliente e escalável, servindo como a "fonte da verdade" para o estado das competições, usuários e exercícios.

## 🚀 Funcionalidades Principais

O Interpreter gerencia os seguintes módulos do ecossistema:

* **Gestão de Identidade (`auth`)**: Persistência de perfis de usuários e credenciais.
* **Orquestração de Competições (`competitions`)**: Gerenciamento de eventos de CTF e seus participantes.
* **Repositório de exercícios (`exercises`)**: Cadastro e metadados de exercícios técnicos.
* **Controle de Infraestrutura (`containers`)**: Mapeamento de instâncias Docker para exercícios específicos.
* **Pontuação em Tempo Real (`scoreboard` & `solves`)**: Registro de submissões de flags e cálculo dinâmico de ranking.
* **Gestão de Engajamento (`attendance`)**: Registro de presença de alunos em atividades da entidade.
* **Taxonomia (`tags`)**: Organização de conteúdos por categorias e níveis de dificuldade.

## 🛠️ Stack Tecnológica

* **Linguagem**: Python 3.x
* **Framework Web**: [FastAPI](https://fastapi.tiangolo.com/) (Alta performance e documentação automática)
* **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) (Mapeamento objeto-relacional)
* **Banco de Dados**: [MariaDB](https://mariadb.org/)
* **Containerização**: Docker & Docker Compose

## 🏗️ Arquitetura e Resiliência

O Interpreter possui um mecanismo nativo de **Retry Logic** para conexão com o banco de dados:

* Ao iniciar, o serviço tenta se conectar ao MariaDB até 10 vezes com intervalos de 3 segundos.
* Isso evita falhas de inicialização em ambientes orquestrados (como Docker Compose) onde o banco de dados pode demorar alguns segundos extras para estar pronto para conexões.


## 📦 Como Executar

### Via Docker (Recomendado)

O Interpreter faz parte do ecossistema Lycosidae e deve ser preferencialmente executado através do arquivo `compose.yaml` na raiz do projeto principal:

```bash
docker-compose up -d interpreter

```

O serviço estará disponível internamente na rede Docker na porta `8000` e mapeado para a porta `8080` no host por padrão.

### Localmente (Desenvolvimento)

1. Instale as dependências:
```bash
pip install -r requirements.txt

```


2. Configure a variável `DATABASE_URL` no seu ambiente.
3. Execute o script de inicialização:
```bash
./uvicorn.sh

```



## 📖 Documentação da API

Uma vez que o serviço esteja rodando, você pode acessar a documentação interativa (Swagger UI) fornecida pelo FastAPI no endpoint:

* **URL**: `http://localhost:8080/docs`

## 🛡️ Licença

Este projeto está licenciado sob os termos da licença incluída no arquivo `LICENSE`.