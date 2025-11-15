# Site do NEMO

Bem-vindo ao repositório oficial do site do NEMO (Núcleo de Estudos de Matemática Olímpica), um grupo de extensão da USP de São Carlos dedicado à matemática competitiva e à resolução de problemas.

## Sobre Este Projeto

Este projeto é uma aplicação web baseada em Flask que serve como uma das presenças online do NEMO. Ele possui um blog para notícias e artigos, uma seção para os Problemas do Mês e páginas com informações sobre o grupo, seus membros e materiais de estudo.

## Funcionalidades

-   **Gerenciamento de Conteúdo Dinâmico:** Posts de blog são gerenciados com Flask-FlatPages (arquivos Markdown), enquanto itens de materiais são gerenciados via banco de dados SQL.
-   **Autenticação de Usuários:** O site possui um sistema completo de autenticação de usuários, permitindo que membros façam login e gerenciem o conteúdo.
-   **Editor de Posts:** Um editor de Markdown no navegador está disponível para criar e editar publicações.
-   **Implantação com Docker:** A aplicação é totalmente containerizada com Docker e pronta para implantação em produção com o Gunicorn.
-   **Segurança Integrada:** A aplicação inclui proteção contra CSRF em todos os formulários e sanitiza o conteúdo gerado por usuários para prevenir ataques de XSS.

---

## 🚀 Instruções de Implantação (Vultr + Docker)

Este é o guia padrão para implantar o site em um novo servidor Ubuntu (como o Vultr).

### Estágio 1: 🖥️ Configuração Inicial do Servidor

1.  **Acesse seu servidor** (via SSH ou console Vultr):
    ```bash
    # Substitua 'root' e 'seu_ip_do_servidor'
    ssh root@seu_ip_do_servidor
    ```

2.  **Crie um usuário administrador:**
    ```bash
    # Substitua 'nemo_admin' pelo seu nome de usuário
    adduser nemo_admin
    usermod -aG sudo nemo_admin
    ```

3.  **Configure o Firewall (UFW):**
    *Nota: Fizemos isso antes de instalar o NGINX, então abrimos as portas manualmente.*
    ```bash
    sudo ufw allow OpenSSH
    sudo ufw allow 80/tcp     # HTTP
    sudo ufw allow 443/tcp    # HTTPS
    sudo ufw enable         # Digite 'y' para confirmar
    ```

4.  **Atualize o servidor:**
    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```

5.  **Re-login como seu novo usuário:**
    Saia da sessão `root` e entre com seu novo usuário.
    ```bash
    exit
    ssh nemo_admin@seu_ip_do_servidor
    ```

### Estágio 2:  DNS (Porkbun)

1.  **Faça login no Porkbun** e vá para os registros DNS de `nemo-usp.org`.
2.  **Exclua** quaisquer registros "A" padrão que estejam lá.
3.  **Crie dois novos registros "A":**

    * **Registro 1 (Raiz):**
        * **Tipo:** `A`
        * **Host:** `@`
        * **Resposta:** `SEU_IP_DO_SERVIDOR_VULTR`
    * **Registro 2 (www):**
        * **Type:** `A`
        * **Host:** `www`
        * **Resposta:** `SEU_IP_DO_SERVIDOR_VULTR`

### Estágio 3: 📦 Instalar Docker e Obter o Código

1.  **Instale Git e Docker:**
    ```bash
    sudo apt install git docker.io
    ```

2.  **Adicione seu usuário ao grupo Docker:**
    Isso permite que você execute comandos `docker` sem `sudo`.
    ```bash
    sudo usermod -aG docker ${USER}
    ```

3.  **LOG OUT E LOG BACK IN:**
    Você **deve** sair e entrar novamente no SSH para que a alteração do grupo tenha efeito.
    ```bash
    exit
    ssh nemo_admin@seu_ip_do_servidor
    ```

4.  **Clone seu repositório:**
    ```bash
    git clone <url-do-seu-repositorio-github>
    cd <nome-do-seu-repositorio>  # ex: cd nemo
    ```

### Estágio 4: 📂 Preparar Dados Persistentes

Vamos criar os arquivos e pastas que o Docker precisa *antes* de executá-lo.

1.  **Crie o arquivo `.env`:**
    ```bash
    nano .env
    ```
    Cole o seguinte conteúdo. **NÃO use aspas** e mude a `SECRET_KEY` para algo aleatório.

    ```env
    # Use uma chave aleatória e forte aqui
    SECRET_KEY=sua_chave_super_secreta_aqui
    # Use o caminho absoluto DENTRO do container
    DATABASE_URL=sqlite:////app/instance/posts.db
    ```
    *Salve (Ctrl+O) e Saia (Ctrl+X).*

2.  **Crie as pastas de volume:**
    ```bash
    mkdir -p instance
    mkdir -p static/uploads
    ```

3.  **Corrija as permissões da `instance`:**
    Isso é crucial para permitir que o container crie o arquivo `.db`.
    ```bash
    sudo chmod -R 777 instance/
    ```

4.  **Construa a Imagem Docker:**
    ```bash
    docker build -t nemo-app .
    ```

5.  **Inicialize o Banco de Dados (Usando Docker):**
    Este comando executa o `flask db upgrade` *dentro* do container para criar seu `posts.db` com as tabelas corretas.
    ```bash
    docker run --rm \
      -v $(pwd)/instance:/app/instance \
      -v $(pwd)/posts:/app/posts \
      --env-file .env \
      nemo-app \
      flask db upgrade
    ```

### Estágio 5: 🚀 Executar a Aplicação

Agora vamos iniciar o container de produção no modo "detached" (em segundo plano).

1.  **Remova qualquer container antigo (se houver):**
    ```bash
    docker rm -f nemo-app-prod
    ```
    *(Não se preocupe se disser "No such container".)*

2.  **Inicie o container de produção:**
    ```bash
    docker run -d --restart always \
      -p 127.0.0.1:8000:8000 \
      -v $(pwd)/posts:/app/posts \
      -v $(pwd)/instance:/app/instance \
      -v $(pwd)/static/uploads:/app/static/uploads \
      --env-file .env \
      --name nemo-app-prod \
      nemo-app
    ```

### Estágio 6: 🌐 Configurar NGINX e HTTPS

1.  **Instale o NGINX:**
    ```bash
    sudo apt install nginx
    ```

2.  **Crie o arquivo de configuração do NGINX:**
    ```bash
    sudo nano /etc/nginx/sites-available/nemo-usp.org
    ```
    Cole a seguinte configuração:
    ```nginx
    server {
        listen 80;
        server_name nemo-usp.org www.nemo-usp.org;

        location / {
            proxy_pass [http://127.0.0.1:8000](http://127.0.0.1:8000);
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

3.  **Habilite o site:**
    ```bash
    sudo ln -s /etc/nginx/sites-available/nemo-usp.org /etc/nginx/sites-enabled/
    ```

4.  **Teste e reinicie o NGINX:**
    ```bash
    sudo nginx -t
    sudo systemctl restart nginx
    ```
    *Neste ponto, `http://nemo-usp.org` deve estar funcionando (se o DNS tiver propagado).*

5.  **Instale o Certificado SSL (HTTPS):**
    ```bash
    sudo apt install certbot python3-certbot-nginx
    ```

6.  **Execute o Certbot:**
    ```bash
    sudo certbot --nginx -d nemo-usp.org -d www.nemo-usp.org
    ```
    * Siga as instruções: insira seu e-mail, concorde com os termos (`Y`), e **escolha a opção `2` (Redirecionar)** para forçar o HTTPS.

Seu site agora está no ar e seguro!

---

## ## 🐛 Solução de Erros Comuns (Debugging)

**Erro: `permission denied while trying to connect to the Docker daemon socket...`**
* **Causa:** Você não tem permissão para usar o Docker.
* **Solução:** Adicione seu usuário ao grupo `docker` com `sudo usermod -aG docker ${USER}` e, em seguida, **faça log out e log in novamente**. Como alternativa rápida, use `sudo` antes de todos os comandos `docker`.

**Erro: `sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL from string ''...''`**
* **Causa:** Você usou aspas no seu arquivo `.env`.
* **Solução:** Abra o `nano .env` e remova as aspas. Deve ser `CHAVE=VALOR`, não `CHAVE='VALOR'`.

**Erro: `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file`**
* **Causa 1:** O `DATABASE_URL` no `.env` está usando um caminho relativo (ex: `sqlite:///instance/posts.db`).
* **Solução 1:** Use o caminho absoluto *dentro* do container: `DATABASE_URL=sqlite:////app/instance/posts.db`.
* **Causa 2:** O container Docker não tem permissão para escrever na pasta `instance/` do host.
* **Solução 2:** Execute `sudo chmod -R 777 instance/` no seu servidor (host).

**Erro: `Conflict. The container name "/nemo-app-prod" is already in use...`**
* **Causa:** Um container antigo e parado com esse nome já existe.
* **Solução:** Remova o container antigo antes de iniciar um novo: `docker rm nemo-app-prod`.

**Erro: `Certbot failed to authenticate... Type: unauthorized`**
* **Causa:** Seus registros DNS no Porkbun ainda não estão apontando para o IP do seu servidor Vultr.
* **Solução:** Siga o **Estágio 2** com cuidado. Aguarde 10-30 minutos para o DNS propagar. Você pode verificar com o comando `ping nemo-usp.org` (no seu PC local) para ver se o IP correto é exibido.
