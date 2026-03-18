# ✅ Gerenciamento de Rotina

Aplicação web desenvolvida com **Flask + SQLite** para controle de tarefas diárias, atividades paralelas, metas globais e anotações — tudo organizado por dia e com acompanhamento de progresso em tempo real.

---

## 🚀 Funcionalidades

- 📅 Controle de tarefas por data
- 🔁 Tarefas recorrentes (rotina fixa)
- 📊 Indicadores de progresso:
  - Início do turno
  - Meio do turno
  - Final do turno
  - Progresso geral
- 🖇️ Atividades paralelas
- 🌍 Atividades globais com prazo
- 📝 Sistema de anotações diárias
- 🌙 Tema claro/escuro (Dark Mode)
- 🚀 Inicialização automática de rotina
- ✔️ Validação para finalização do turno

---

## 🧠 Regras de Negócio

- O turno só pode ser finalizado se **todas as tarefas e atividades paralelas estiverem concluídas**
- Tarefas recorrentes são carregadas automaticamente ao iniciar o turno
- O progresso é calculado com base nas tarefas concluídas

---

## 🛠️ Tecnologias Utilizadas

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- HTML5 + CSS3 + JavaScript

---

## 📁 Estrutura do Projeto

📦 gerenciamento-rotina
├── app.py
├── gerenciamento_rotina.db
├── templates/
│ └── index.html
└── static/ (opcional)

---

## ⚙️ Como Executar o Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/Guilherme-Castro987/Gerenciamento-de-rotina-com-Python-e-Flask.git
cd seu-repo
