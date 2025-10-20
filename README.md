# 🏢 Sistema de Hierarquia Organizacional

Um sistema web completo desenvolvido em **Django** com **HTML, CSS e JavaScript** para gerenciar a estrutura hierárquica de uma organização, controle de acesso baseado em cargos e gestão de requisições.

## 📋 Características

### ✅ Funcionalidades Principais

- **Autenticação e Login**: Sistema seguro de autenticação com Django
- **Cadastro de Funcionários**: Formulário completo com validação de CPF
- **Hierarquia Organizacional**: Estrutura de 5 níveis (Diretor, Gestor, Coordenador, Supervisor, ADM)
- **Controle de Acesso**: Visualização e gerenciamento baseado em cargo e setor
- **Requisições**: Sistema de requisições com aprovação por hierarquia
- **Dashboard**: Visão geral com estatísticas
- **Gerenciamento**: Cargos, setores e centros de serviço

### 🎨 Interface

- Design moderno e responsivo
- Gradientes e animações suaves
- Suporte completo para mobile
- Validação em tempo real com JavaScript

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)
- Git (opcional)

### Passos de Instalação

1. **Extrair o arquivo ZIP**
```bash
unzip sistema_hierarquia_completo.zip
cd sistema_hierarquia
```

2. **Criar ambiente virtual**
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. **Instalar dependências**
```bash
pip install --upgrade pip
pip install django djangorestframework python-decouple pillow
```

4. **Executar migrações do banco de dados**
```bash
python manage.py migrate
```

5. **Criar superusuário (Admin)**
```bash
python manage.py createsuperuser
```

Siga as instruções para criar um usuário admin.

6. **Iniciar o servidor**
```bash
python manage.py runserver
```

7. **Acessar a aplicação**
```
http://localhost:8000/login/
```

## 🔐 Credenciais Padrão

Se você usar o banco de dados incluído no ZIP:

- **Usuário**: admin
- **Senha**: admin123

**⚠️ Importante**: Altere a senha após o primeiro login!

## 📊 Estrutura de Hierarquia

### Níveis de Acesso

| Nível | Cargo | Visualiza | Gerencia |
|-------|-------|-----------|----------|
| 1 | Diretor | Todos | Todos |
| 2 | Gestor | Coordenadores, Supervisores, ADMs | Sua equipe |
| 3 | Coordenador | Supervisores, ADMs | Sua equipe |
| 4 | Supervisor | ADMs | Sua equipe |
| 5 | ADM/Analista | - | Requisições |

## 📁 Estrutura do Projeto

```
sistema_hierarquia/
├── config/                          # Configurações Django
│   ├── settings.py                 # Configurações principais
│   ├── urls.py                     # URLs principais
│   ├── asgi.py                     # ASGI config
│   └── wsgi.py                     # WSGI config
│
├── hierarquia/                      # Aplicação principal
│   ├── models.py                   # Modelos de dados
│   ├── views.py                    # Lógica de negócio
│   ├── urls.py                     # URLs da app
│   ├── admin.py                    # Admin Django
│   └── migrations/                 # Migrações do BD
│
├── templates/hierarquia/            # Templates HTML
│   ├── login.html                  # Tela de login
│   ├── dashboard.html              # Dashboard principal
│   ├── listar_funcionarios.html    # Lista de funcionários
│   └── cadastrar_funcionario.html  # Cadastro de funcionário
│
├── manage.py                        # Gerenciador Django
├── db.sqlite3                       # Banco de dados (SQLite)
└── README.md                        # Este arquivo
```

## 🗄️ Modelos de Dados

### Cargo
- Nome único
- Nível hierárquico (1-5)
- Descrição

### Setor
- Nome único
- Descrição

### Centro de Serviço
- Nome
- Setor (relacionado)
- Descrição

### Funcionário
- Nome
- CPF (único, validado)
- Data de nascimento
- Data de admissão
- Cargo (relacionado)
- Setor (relacionado)
- Centro de serviço (opcional)
- Status (ativo/inativo)

### Requisição
- Título
- Descrição
- Solicitante (funcionário)
- Status (pendente, aprovada, rejeitada, concluída)
- Aprovador (funcionário)
- Data de aprovação

## 🔧 Configuração

### Alterar Banco de Dados

Para usar PostgreSQL em produção, edite `config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'seu_banco',
        'USER': 'seu_usuario',
        'PASSWORD': 'sua_senha',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Instale o driver:
```bash
pip install psycopg2-binary
```

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,seu-dominio.com
```

## 📝 Uso da Aplicação

### 1. Login
- Acesse `http://localhost:8000/login/`
- Digite suas credenciais

### 2. Dashboard
- Visualize estatísticas gerais
- Acesse menu principal

### 3. Funcionários
- Liste todos os funcionários (conforme sua hierarquia)
- Busque por nome
- Cadastre novos funcionários (apenas admin)
- Visualize detalhes e hierarquia

### 4. Requisições
- Crie novas requisições
- Visualize suas requisições
- Aprove/rejeite requisições (conforme hierarquia)

### 5. Configurações (Admin)
- Gerenciar cargos
- Gerenciar setores
- Gerenciar centros de serviço

## 🛡️ Segurança

### Recomendações para Produção

1. **Altere a SECRET_KEY** em `config/settings.py`
2. **Configure DEBUG = False**
3. **Use HTTPS**
4. **Configure ALLOWED_HOSTS** com seus domínios
5. **Use um banco de dados robusto** (PostgreSQL)
6. **Configure variáveis de ambiente** para dados sensíveis
7. **Implemente rate limiting** para login
8. **Configure CSRF protection**
9. **Use senhas fortes** para admin
10. **Faça backup regular** do banco de dados

## 🚀 Deploy

### Usando Gunicorn + Nginx

1. Instale Gunicorn:
```bash
pip install gunicorn
```

2. Execute:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

3. Configure Nginx como proxy reverso

### Usando Docker

Crie um `Dockerfile`:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 📚 Documentação Django

- [Django Docs](https://docs.djangoproject.com/)
- [Django Models](https://docs.djangoproject.com/en/stable/topics/db/models/)
- [Django Views](https://docs.djangoproject.com/en/stable/topics/http/views/)
- [Django Templates](https://docs.djangoproject.com/en/stable/topics/templates/)

## 🐛 Troubleshooting

### Erro: "No module named 'django'"
```bash
pip install django
```

### Erro: "ModuleNotFoundError"
Certifique-se de que o ambiente virtual está ativado:
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Erro: "Port 8000 already in use"
```bash
python manage.py runserver 8001
```

### Resetar banco de dados
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação do Django
2. Consulte os logs do servidor
3. Verifique se todas as dependências estão instaladas

## 📄 Licença

Este projeto é fornecido como está para fins educacionais e comerciais.

## ✨ Melhorias Futuras

- [ ] Editar e deletar funcionários
- [ ] Relatórios em PDF
- [ ] Exportar dados em Excel
- [ ] Notificações por email
- [ ] API REST completa
- [ ] Testes automatizados
- [ ] Integração com LDAP/Active Directory
- [ ] Dashboard com gráficos
- [ ] Auditoria de ações

---

**Desenvolvido com ❤️ usando Django, HTML, CSS e JavaScript**
