# Deploy KaziLayer from GitHub to CloudPanel with SSH

This guide deploys the Next.js frontend and Django backend on one CloudPanel server. CloudPanel sends public traffic to Next.js on port `3000`. NGINX sends `/api/` requests to Django on port `8000`, so sessions and CSRF cookies stay on one domain.

**Document type:** How-to  
**Audience:** A server administrator with CloudPanel and DNS access  
**Last verified:** 9 October 2026

## Deployment layout

| Layer | Runtime | Listener | Process owner |
|---|---|---:|---|
| Public web application | Next.js 16 | `127.0.0.1:3000` | PM2 under the CloudPanel site user |
| Application programming interface (API) | Django ASGI with Uvicorn | `127.0.0.1:8000` | systemd under the same site user |
| Database | Neon PostgreSQL | Managed service | Neon |
| TLS and public routing | CloudPanel NGINX | `80` and `443` | CloudPanel |

The backend ports stay private. Only NGINX accepts public traffic.

## Prerequisites

Prepare these values before you connect:

- A server supported by CloudPanel with ports `22`, `80`, and `443` available
- A domain with an `A` or `AAAA` record pointing to the server
- A CloudPanel administrator account
- A Neon PostgreSQL connection string with `sslmode=require`
- The GitHub repository `danielmg29/kazilayer`
- A Linux account with `sudo` access for the Django systemd service

This repository requires Python `3.13` or newer. Select a current Node.js release that satisfies Next.js 16. CloudPanel manages Node versions with Node Version Manager (NVM).

## Fix the production settings before deployment

The current development settings set `DEBUG = True` and do not define `STATIC_ROOT`. Do not expose the backend until the deployment branch reads debug mode from the environment.

Update `backend/config/settings.py` on the deployment branch:

```python
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

Keep `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` tied to `not DEBUG`. Run Django's deployment check before every release.

## Create the CloudPanel site

CloudPanel supports Node.js sites with a selected Node version and application port. Create one Node.js site for the public domain:

1. Open **Sites** in CloudPanel.
2. Click **Add Site**.
3. Select **Create a Node.js Site**.
4. Enter the production domain.
5. Select the current supported Node.js version.
6. Set **App Port** to `3000`.
7. Save the generated site-user credentials.

CloudPanel redirects HTTP to HTTPS after you issue a valid certificate. Point DNS to the server before requesting the certificate.

Reference: [CloudPanel: Add Site](https://www.cloudpanel.io/docs/v2/frontend-area/add-site/)

## Connect to the CloudPanel site user

CloudPanel creates a dedicated Secure Shell (SSH) user for the site. Add your public key under **Site > SSH/FTP**, then connect:

```bash
ssh cloudpanel_site_user@server_ip_address
```

CloudPanel uses SSH port `22` by default. Restrict that port to trusted IP addresses in the server firewall.

Reference: [CloudPanel: SSH/FTP](https://www.cloudpanel.io/docs/v2/frontend-area/ssh-ftp/)

## Give the server read-only GitHub access

Generate a dedicated key as the CloudPanel site user. Do not reuse a personal workstation key.

```bash
ssh-keygen -t ed25519 -C "kazilayer-cloudpanel" \
  -f ~/.ssh/kazilayer_github
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/kazilayer_github
cat ~/.ssh/kazilayer_github.pub
```

In GitHub, open **Repository settings > Deploy keys > Add deploy key**. Paste the public key and leave write access disabled.

Create `~/.ssh/config`:

```sshconfig
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/kazilayer_github
  IdentitiesOnly yes
```

Set secure permissions and test the connection:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/config ~/.ssh/kazilayer_github
chmod 644 ~/.ssh/kazilayer_github.pub
ssh -T git@github.com
```

GitHub should identify the repository or account and state that shell access is unavailable.

References: [GitHub: Generate an SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent), [GitHub: Test an SSH connection](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection)

## Clone the repository

Store the repository below the CloudPanel site directory. Replace the placeholders with the values CloudPanel created.

```bash
cd /home/cloudpanel_site_user/htdocs/your_domain
git clone git@github.com:danielmg29/kazilayer.git app
cd app
git switch main
```

Confirm that `git remote -v` uses the `git@github.com:` SSH URL.

## Configure and build Django

Install `uv` as the site user, then synchronize the locked environment:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.profile
cd /home/cloudpanel_site_user/htdocs/your_domain/app/backend
uv sync --frozen
```

Reference: [uv: Installation](https://docs.astral.sh/uv/getting-started/installation/)

Create `backend/.env` and restrict access:

```dotenv
DATABASE_URL=postgresql://database_user:database_password@database_host/database_name?sslmode=require
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=replace_with_a_random_secret
DJANGO_ALLOWED_HOSTS=your_domain,www.your_domain,127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://your_domain,https://www.your_domain
KAZILAYER_MFA_ENCRYPTION_KEY=replace_with_a_fernet_key
```

Generate secrets on the server:

```bash
uv run python -c "import secrets; print(secrets.token_urlsafe(64))"
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
chmod 600 .env
```

Apply migrations and collect static files:

```bash
uv run python manage.py check --deploy
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
```

For a demo installation only, load the six-month dataset once:

```bash
uv run python manage.py seed_neon_demo
```

Do not run the demo seed command against a live customer database.

## Run Django with systemd

Use Uvicorn because this repository exposes an Asynchronous Server Gateway Interface (ASGI) application. Run the following steps with `sudo` access.

Create `/etc/systemd/system/kazilayer-api.service`:

```ini
[Unit]
Description=KaziLayer Django API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=cloudpanel_site_user
Group=cloudpanel_site_user
WorkingDirectory=/home/cloudpanel_site_user/htdocs/your_domain/app/backend
EnvironmentFile=/home/cloudpanel_site_user/htdocs/your_domain/app/backend/.env
ExecStart=/home/cloudpanel_site_user/htdocs/your_domain/app/backend/.venv/bin/uvicorn config.asgi:application --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kazilayer-api
sudo systemctl status kazilayer-api
curl -I http://127.0.0.1:8000/api/v1/csrf/
```

Reference: [Django 6.1: Deploy with Uvicorn](https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/uvicorn/)

## Configure and run Next.js

Install the package manager version declared by the repository and build the frontend:

```bash
cd /home/cloudpanel_site_user/htdocs/your_domain/app/frontend
npm install --global pnpm@11.24.0 pm2@latest
pnpm install --frozen-lockfile
```

Create `frontend/.env.production`:

```dotenv
KAZILAYER_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_SITE_URL=https://your_domain
```

Build and start the production server:

```bash
pnpm build
pm2 start npm --name kazilayer-web -- start -- --port 3000
pm2 save
pm2 status
```

Configure PM2 to restore the process after a reboot. CloudPanel documents a site-user crontab using `pm2 resurrect`:

```bash
echo "$PATH"
crontab -e
```

Add the reported `PATH` and the restore command:

```cron
PATH=copy_the_path_reported_by_the_previous_command
@reboot pm2 resurrect >/dev/null 2>&1
```

References: [CloudPanel: Node.js with PM2](https://www.cloudpanel.io/docs/v2/nodejs/deployment/pm2/), [Next.js: Deploying](https://nextjs.org/docs/app/getting-started/deploying), [Next.js: Self-hosting](https://nextjs.org/docs/app/guides/self-hosting)

## Route API and media traffic in CloudPanel

Open **Site > Vhost**. Keep CloudPanel's generated TLS and server settings. Add these locations before the general Next.js `location /` block:

```nginx
location ^~ /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location ^~ /media/ {
    alias /home/cloudpanel_site_user/htdocs/your_domain/app/backend/media/;
    access_log off;
    expires 7d;
}

location ^~ /static/ {
    alias /home/cloudpanel_site_user/htdocs/your_domain/app/backend/staticfiles/;
    access_log off;
    expires 30d;
}
```

CloudPanel validates NGINX syntax and reverts invalid Vhost edits. The generated `location /` block must continue proxying to `127.0.0.1:3000`.

Reference: [CloudPanel: Vhost Editor](https://www.cloudpanel.io/docs/v2/frontend-area/vhost/)

## Issue TLS and verify the deployment

Issue a Let's Encrypt certificate in **Site > SSL/TLS** after DNS resolves to the server. Then verify the application:

```bash
curl -I https://your_domain/
curl -I https://your_domain/api/v1/csrf/
curl -I https://your_domain/login
sudo systemctl status kazilayer-api
pm2 status
```

Check these browser flows:

1. Open the landing page.
2. Sign in with a demo account.
3. Open a tenant workspace.
4. Upload and retrieve an image.
5. Confirm that `/api/` requests return no redirect loop.
6. Confirm that cookies use `Secure` and the production domain.

## Deploy an update

Run updates as the CloudPanel site user:

```bash
cd /home/cloudpanel_site_user/htdocs/your_domain/app
git fetch origin
git pull --ff-only origin main

cd backend
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
sudo systemctl restart kazilayer-api

cd ../frontend
pnpm install --frozen-lockfile
pnpm build
pm2 restart kazilayer-web --update-env
```

Run database migrations before restarting the frontend when a release changes the API contract.

## Roll back a failed release

Record the current commit before each deployment:

```bash
git rev-parse HEAD
```

To restore a known release, check out its commit, rebuild both environments, and restart both processes:

```bash
git checkout known_good_commit_sha
cd backend && uv sync --frozen
sudo systemctl restart kazilayer-api
cd ../frontend && pnpm install --frozen-lockfile && pnpm build
pm2 restart kazilayer-web --update-env
```

Do not reverse a database migration until you confirm that the migration is reversible and no newer data depends on it.

## Troubleshoot the deployment

Use these commands to locate failures:

```bash
pm2 logs kazilayer-web --lines 100
sudo journalctl -u kazilayer-api -n 100 --no-pager
sudo nginx -t
curl -v http://127.0.0.1:3000/
curl -v http://127.0.0.1:8000/api/v1/csrf/
```

- A `502` response means NGINX cannot reach the configured application port.
- A Django `400 Bad Request` usually means the domain is missing from `DJANGO_ALLOWED_HOSTS`.
- A login `403` usually means the HTTPS origin is missing from `DJANGO_CSRF_TRUSTED_ORIGINS`.
- A redirect loop usually means the proxy changed the API trailing slash or omitted `X-Forwarded-Proto`.
- Missing avatars or evidence files usually mean the `/media/` Vhost location points to the wrong directory.

## Source documentation

This guide was checked against the current official documentation on 9 October 2026:

- [CloudPanel: Add Site](https://www.cloudpanel.io/docs/v2/frontend-area/add-site/)
- [CloudPanel: SSH/FTP](https://www.cloudpanel.io/docs/v2/frontend-area/ssh-ftp/)
- [CloudPanel: Vhost Editor](https://www.cloudpanel.io/docs/v2/frontend-area/vhost/)
- [CloudPanel: Node.js with PM2](https://www.cloudpanel.io/docs/v2/nodejs/deployment/pm2/)
- [GitHub: Connecting with SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Next.js: Deploying](https://nextjs.org/docs/app/getting-started/deploying)
- [Next.js: Self-hosting](https://nextjs.org/docs/app/guides/self-hosting)
- [Django 6.1: Deployment checklist](https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/)
- [Django 6.1: Deploy with Uvicorn](https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/uvicorn/)
