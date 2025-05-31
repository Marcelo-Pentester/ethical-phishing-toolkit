# 🎣 Phishing Toolkit


**Phishing Toolkit** é uma ferramenta completa para simulação de ataques de phishing com foco em **fins educacionais**, **treinamentos de conscientização** e **testes autorizados de segurança ofensiva**.

> ⚠️ **AVISO LEGAL:** Esta ferramenta é estritamente para **uso educacional** e **testes de segurança autorizados**. O uso em ambientes sem consentimento explícito é ilegal e contra os termos de uso.

## 📌 Funcionalidades

- 🎯 Gerenciamento de alvos (targets)
- 🌐 Servidor de phishing com **templates customizáveis**
- 📊 Dashboard com monitoramento em **tempo real**
- 📍 Geolocalização de acessos (baseada em IP)
- 📄 Geração automática de **relatórios em PDF**
- 🔍 Captura e armazenamento de **credenciais**
- 🕵️ Rastreamento por **cookies** e **tokens únicos**

## 📦 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/phishing-toolkit.git
cd phishing-toolkit
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

#### `requirements.txt`

```txt
requests==2.31.0
fpdf2==2.7.4
sqlite3==2.6.0
python-dotenv==1.0.0

# (Para testes e desenvolvimento)
pytest==7.4.0
```

## 🚀 Como Usar

Execute a ferramenta a partir do terminal:

```bash
python phishing_toolkit.py
```

Você verá o seguinte menu interativo:

```
=== Phishing Toolkit ===
1. Adicionar novo target
2. Executar simulação
3. Gerar relatório
4. Iniciar servidor de phishing
5. Ver credenciais capturadas
6. Iniciar dashboard de rastreamento
7. Sair
```

## 🛠️ Estrutura do Projeto

```
phishing-toolkit/
├── phishing_toolkit.py       # Código principal
├── db.sqlite                 # Banco de dados local
├── phishing_site/            # Templates HTML de phishing
│   └── index.html
├── reports/                  # Relatórios PDF gerados
├── requirements.txt          # Dependências Python
├── LICENSE                   # Licença do projeto (MIT)
├── README.md                 # Este arquivo
└── docs/                     # Documentação extra (opcional)
```

## 🌍 Templates Disponíveis

- Facebook
- Gmail

> Adicione seus próprios templates na pasta `phishing_site/`.

## 📊 Dashboard

Visualize os dados capturados em tempo real no dashboard local:

**🔗 Acesse:** `http://localhost:5000`

> ![Preview do Dashboard](images/dashboard-preview.png)

## 📝 Relatórios

Relatórios são gerados automaticamente em `reports/` com:

- ✅ Lista de alvos
- 🔐 Credenciais capturadas
- 🌐 Informações de geolocalização
- 🕓 Histórico de cliques

> ![Exemplo de Relatório](images/report-example.png)

## ⚠️ Limitações e Avisos

- ❌ Não use a ferramenta sem permissão explícita do sistema alvo
- 📍 Geolocalização baseada em IP pode ter limitações de precisão
- 👮 Atividades ilegais podem resultar em **consequências legais severas**

## 🤝 Contribuição

Contribuições são bem-vindas! Siga os passos abaixo:

```bash
# 1. Faça um fork
# 2. Crie uma branch para sua feature:
git checkout -b feature/NomeDaFeature

# 3. Commit e push:
git commit -m 'Add NovaFeature'
git push origin feature/NomeDaFeature

# 4. Abra um Pull Request
```

## 📄 Licença

Distribuído sob a [Licença MIT](LICENSE).

## ✉️ Contato

**Seu Nome** – [@seu_twitter](https://twitter.com/seu_twitter) – seu-email@exemplo.com  
**Projeto:** [github.com/seu-usuario/phishing-toolkit](https://github.com/seu-usuario/phishing-toolkit)

## 📚 Recursos Adicionais

Considere criar a pasta `docs/` com os seguintes arquivos:

- `docs/templates.md` – Como criar e usar templates personalizados
- `docs/api.md` – Documentação da API interna (caso exista)
- `docs/deployment.md` – Guia de implantação em ambientes reais ou isolados

## 🖼️ Imagens Sugeridas

Crie a pasta `images/` com:

- `dashboard-preview.png` – Captura de tela do dashboard
- `report-example.png` – Exemplo de relatório em PDF
