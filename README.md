# Interpreter-Lycosidae

Serviço backend do projeto **Lycosidae CTF**, responsável pela lógica de negócio e pela abstração da comunicação com o banco de dados **MariaDB**, utilizando **FastAPI** e **SQLAlchemy**.

O sistema adota uma **arquitetura modular baseada em Routers**, expondo endpoints organizados por domínio (Auth, Competitions, Exercises) para gerir o ciclo de vida dos desafios, equipes e submissões de flags com segurança reforçada.

## ✨ Funcionalidades Implementadas

### 🔧 Core & Segurança

- **Autenticação**: Registro e login para usuários da plataforma.
- **Context Shielding**: Proteção contra submissão de flags cruzadas.

### 🏆 Gestão de Competições

- **Sistema de Convites**: Entrada em competições através de códigos únicos.
- **Scoreboard em Tempo Real**: Ranking dinâmico de equipes ordenado por pontuação.
- **Gestão de Equipes**: Criação, associação de membros e cálculo automático de *score* de equipe.

### 💪 Jogabilidade (CTF)

- **Distribuição de Exercícios**: Listagem de desafios filtrada por competição e estado de resolução.
- **Validação de Flags**: Sistema transacional de submissão que valida a flag, o tempo e a unicidade da solução.
- **Infraestrutura Dinâmica**: Endpoint dedicado para recuperar dados de conexão (IP/Porta) de desafios baseados em containers.

### 📊 Logs Estruturados

- **Sistema de logging centralizado** em `app/logger.py`.
- **Métricas de performance** (tempo de resposta dos endpoints).
- **Logs coloridos** para desenvolvimento e **JSON** para produção.
- **Rastreabilidade** de erros críticos e tentativas de *bypass*.

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.9+
- MariaDB/MySQL
- Docker (opcional)

### Instalação

```bash
# Clone o repositório
git clone <repository-url>
cd Interpreter-Lycosidae

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# IMPORTANTE: Defina a variável PASS_SALT no .env para a segurança das senhas

# Execute o servidor
./uvicorn.sh

```

### Acessar a Documentação

* **Swagger UI**: [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](https://www.google.com/search?q=http://localhost:8000/redoc)
* **Health Check**: [http://localhost:8000/](https://www.google.com/search?q=http://localhost:8000/)

---

## 📡 Endpoints da API

A API foi reorganizada em prefixos por domínio.

### 🔐 Autenticação (`/auth`)

* `POST /auth/register` - Registro de novo utilizador (com validação de unicidade).
* `GET /auth/profile/{user_id}` - Consultar perfil público de um utilizador.
* `GET /auth/users/email/{email}` - Consulta de credenciais para login.

### 🏆 Competições (`/competitions`)

* `GET /competitions` - Listar todas as competições.
* `POST /competitions` - Criar nova competição.
* `GET /competitions/{comp_id}` - Consultar detalhes de uma competição.
* `POST /competitions/{comp_id}/join` - Entrar numa competição (valida `invite_code`).
* `GET /competitions/{comp_id}/teams` - Listar equipes de uma competição.
* `POST /competitions/{comp_id}/teams` - Criar nova equipe.
* `POST /competitions/teams/{team_id}/join` - Juntar-se a uma equipe existente.
* `GET /competitions/{comp_id}/scoreboard` - Obter o placar atualizado.

### 💪 Exercícios (`/exercises`)

* `POST /exercises` - Criar exercício na biblioteca global.
* `POST /exercises/{ex_id}/link-competition/{comp_id}` - Associar exercício a uma competição.
* `GET /exercises/competition/{comp_id}` - Listar exercícios ativos (inclui status de resolução).
* `POST /exercises/{ex_id}/submit` - Submeter flag (valida time, competição e exercício).
* `GET /exercises/{ex_id}/connection` - Obter dados de conexão (Host/Porta) do container.

---

## 🏗️ Arquitetura de Execução

* **Modularidade**: A aplicação é iniciada em `app/main.py`, que agrega os routers definidos em `app/routers/`.
* **Configuração**: As variáveis de ambiente (como `DATABASE_URL` e `PASS_SALT`) controlam o comportamento sem alterar o código.
* **Base de Dados**: Sessões geridas via `Depends(get_db)` garantindo o fecho correto das conexões.

---

## 📊 Estrutura de Dados

### Tabelas Principais

| Tabela | Campos Principais | Descrição |
| --- | --- | --- |
| **Users** | username, email, password | Utilizadores do sistema |
| **Competitions** | name, organizer, invite_code, status | Eventos CTF |
| **Teams** | name, score, competition_id, creator_id | Equipes de cada competição |
| **Exercises** | name, description, category, difficulty, flag, points, image_tag | Desafios/Problemas com tag do container Docker |
| **Solves** | submission_content, user_id, team_id, exercise_id, points_awarded | Registro de soluções válidas |
| **Containers** | exercise_id, container_docker_id, image_tag, port_public, connection_command | Dados de conexão da infraestrutura |
| **Tags** | type | Tags de classificação dos exercícios |

### Tabelas de Relacionamento

| Tabela | Relaciona | Descrição |
| --- | --- | --- |
| **user_competitions** | Users ↔ Competitions | Registro de participação |
| **user_teams** | Users ↔ Teams | Membros das equipes |
| **exercise_competitions** | Exercises ↔ Competitions | Exercícios disponíveis no evento |

---

## 🔧 Desenvolvimento

### Estrutura do Projeto

```text
app/
├── main.py              # Entrypoint e agregação de routers
├── database.py          # Configuração da sessão de BD
├── logger.py            # Logging estruturado
├── models.py            # Modelos ORM (SQLAlchemy)
├── schemas.py           # DTOs para validação (Pydantic)
└── routers/             # Módulos de lógica de negócio
    ├── auth.py          # Gestão de utilizadores
    ├── competitions.py  # Competições, Teams e Scoreboard
    └── exercises.py     # Desafios e Submissões

```

### Logs Estruturados

* **Desenvolvimento**: Logs coloridos no console para leitura fácil.
* **Produção**: Logs em JSON para ingestão por ferramentas de monitorização.
* **Contexto**: `request_id` e tempos de execução são registrados automaticamente.

### Segurança e Validação

* **Pydantic Schemas**: Todas as entradas (`payloads`) são estritamente tipadas.
* **Hashing**: As senhas nunca são armazenadas em texto simples.
* **Validação de Negócio**: Verificações lógicas (ex: se o utilizador pertence à equipe que está a tentar pontuar) são feitas antes de qualquer escrita no banco.

---

## 🧪 Testando a API

### Exemplo de Requisição (Novos Endpoints)

```bash
# Registrar um utilizador
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "aluno_test",
    "email": "aluno@insper.edu.br",
    "password": "senha_segura",
    "phone_number": "+551199999999"
  }'

# Criar uma competição (Admin)
curl -X POST "http://localhost:8000/competitions/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Insper CTF 2025",
    "organizer": "Lycosidae Team",
    "invite_code": "INSPER2025",
    "start_date": "2025-01-01T10:00:00",
    "end_date": "2025-01-02T22:00:00"
  }'

```

### Documentação Interativa

Acesse [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs) para testar todos os endpoints, incluindo os novos fluxos de submissão e scoreboard.

---

## 🤝 Contribuição

### Padrões de Código

* **Docstrings** explicativas no início de cada função de rota.
* **Separação de Responsabilidades**: Lógica de banco no router ou controller, modelos em `models.py`.
* **Commits Semânticos**: Utilize prefixos como `feat:`, `fix:`, `refactor:`.

---
