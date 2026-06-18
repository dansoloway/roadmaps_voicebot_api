# Roadmaps Voice API (Python)

FastAPI service that powers voice cloning and narration for Roadmaps.
The PHP app (`roadmaps_daniel/voice/`) calls this at `FISH_API_BASE_URL`.

**Endpoints**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health check |
| POST | `/clone-voice/` | Upload audio → returns `model_id` |
| POST | `/generate-narration/` | `model_id` + `text` → MP3 bytes |

## Run locally

```bash
cd /Users/daniel-new2/sites/roadmaps_voice_python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your key
export $(grep -v '^#' .env | xargs)
uvicorn main:app --host 127.0.0.1 --port 8000
```

Test:

```bash
curl -s http://127.0.0.1:8000/
```

Point PHP at local API: in `roadmaps_daniel/config.php`, set
`FISH_API_BASE_URL` to `http://127.0.0.1:8000` (or use localhost auto-detect).

## Deploy to a new AWS instance

1. Launch Ubuntu/Bitnami Lightsail instance; open ports **22, 80, 443**.
2. Point DNS: `api.roadmaps.fit` → new instance IP.
3. On the server:

```bash
mkdir -p ~/fish_audio_env && cd ~/fish_audio_env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # copy requirements.txt + main.py here first
echo 'FISH_AUDIO_API_KEY=your-key' > .env
uvicorn main:app --host 127.0.0.1 --port 8000   # test
```

4. Nginx (HTTPS → port 8000):

```nginx
server {
    listen 443 ssl;
    server_name api.roadmaps.fit;
    # ssl_certificate ... (certbot)

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```

5. systemd service (`/etc/systemd/system/fish-audio-api.service`):

```ini
[Unit]
Description=Roadmaps Voice API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/fish_audio_env
EnvironmentFile=/home/ubuntu/fish_audio_env/.env
ExecStart=/home/ubuntu/fish_audio_env/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now fish-audio-api
curl -s https://api.roadmaps.fit/
```

## Related code (PHP caller)

- `roadmaps_daniel/voice/api_3/create_voice/index.php` → POST `/clone-voice/`
- `roadmaps_daniel/voice/api_3/create_narration/index.php` → POST `/generate-narration/`
- `roadmaps_daniel/voice/api_3/fish_server_main.py` — duplicate of this `main.py`

## Old server

Previously deployed at **3.134.136.30** (`api.roadmaps.fit`). That instance is down;
all source code is in this repo — nothing was lost on the server except the running process.
