# 🔥 Cloudflare Tunnel Setup for Ollama

## Expose `localhost:11434` as `ollama.mostarindustries.com`

---

## ✅ Prerequisites

- ✅ Domain: `mostarindustries.com` (Active, expires 2026-12-26)
- ✅ Cloudflare DNS: Already configured
- ✅ Ollama running: `localhost:11434`

---

## 📥 Step 1: Install Cloudflared

### Windows Installation

**Download cloudflared**:

```powershell
# Download from GitHub releases
# https://github.com/cloudflare/cloudflared/releases/latest

# Or use winget
winget install --id Cloudflare.cloudflared
```

**Verify installation**:

```powershell
cloudflared --version
```

---

## 🔐 Step 2: Login to Cloudflare

```powershell
cloudflared tunnel login
```

**What happens**:

1. Opens browser to Cloudflare
2. Login with your account (<akiniobong10@gmail.com>)
3. Select `mostarindustries.com`
4. Authorizes cloudflared

**Result**: Creates `cert.pem` in `C:\Users\idona\.cloudflared\`

---

## 🚇 Step 3: Create Tunnel

```powershell
cloudflared tunnel create mostar-ollama
```

**Output**:

```
Tunnel credentials written to C:\Users\idona\.cloudflared\<TUNNEL-ID>.json
Created tunnel mostar-ollama with id <TUNNEL-ID>
```

**Save the TUNNEL-ID** - you'll need it!

---

## 📝 Step 4: Create Configuration File

**Create file**: `C:\Users\idona\.cloudflared\config.yml`

```yaml
tunnel: <TUNNEL-ID>
credentials-file: C:\Users\idona\.cloudflared\<TUNNEL-ID>.json

ingress:
  # Route ollama subdomain to local Ollama
  - hostname: ollama.mostarindustries.com
    service: http://localhost:11434
  
  # Catch-all rule (required)
  - service: http_status:404
```

**Replace `<TUNNEL-ID>`** with your actual tunnel ID from Step 3.

---

## 🌐 Step 5: Create DNS Record

```powershell
cloudflared tunnel route dns mostar-ollama ollama.mostarindustries.com
```

**What this does**:

- Creates a CNAME record in Cloudflare DNS
- Points `ollama.mostarindustries.com` to your tunnel

**Verify in Cloudflare Dashboard**:

1. Go to <https://dash.cloudflare.com>
2. Select `mostarindustries.com`
3. Click **DNS** → **Records**
4. You should see: `ollama` → `<TUNNEL-ID>.cfargotunnel.com`

---

## 🚀 Step 6: Run the Tunnel

### Test Run (Foreground)

```powershell
cloudflared tunnel run mostar-ollama
```

**Expected output**:

```
2026-01-28T10:45:00Z INF Starting tunnel tunnelID=<TUNNEL-ID>
2026-01-28T10:45:01Z INF Connection registered connIndex=0
2026-01-28T10:45:01Z INF Connection registered connIndex=1
2026-01-28T10:45:01Z INF Connection registered connIndex=2
2026-01-28T10:45:01Z INF Connection registered connIndex=3
```

**Test it**:

```powershell
# In another terminal
curl https://ollama.mostarindustries.com/api/tags
```

**Expected**: Should return your Ollama models!

---

## 🔄 Step 7: Run as Windows Service (Permanent)

### Install as Service

```powershell
# Run as Administrator
cloudflared service install
```

### Start Service

```powershell
# Start the service
Start-Service cloudflared

# Check status
Get-Service cloudflared

# Enable auto-start on boot
Set-Service -Name cloudflared -StartupType Automatic
```

### Manage Service

```powershell
# Stop
Stop-Service cloudflared

# Restart
Restart-Service cloudflared

# View logs
cloudflared tail
```

---

## ✅ Step 8: Verify Setup

### Test Ollama API

```powershell
# List models
curl https://ollama.mostarindustries.com/api/tags

# Test generation
curl https://ollama.mostarindustries.com/api/generate -d '{
  "model": "Mostar/mostar-ai:latest",
  "prompt": "Hello in Ibibio",
  "stream": false
}'
```

### Check Tunnel Status

```powershell
cloudflared tunnel list
cloudflared tunnel info mostar-ollama
```

---

## 🔧 Step 9: Update Backend Configuration

### Update `.env` files

**Backend `.env`**:

```bash
OLLAMA_HOST=https://ollama.mostarindustries.com
```

**Supabase Edge Function Secret**:

```bash
# In Supabase Dashboard → Settings → Edge Functions → Secrets
OLLAMA_BASE_URL=https://ollama.mostarindustries.com
```

---

## 🛡️ Security Considerations

### Option 1: Add Authentication (Recommended)

**Update `config.yml`**:

```yaml
tunnel: <TUNNEL-ID>
credentials-file: C:\Users\idona\.cloudflared\<TUNNEL-ID>.json

ingress:
  - hostname: ollama.mostarindustries.com
    service: http://localhost:11434
    originRequest:
      # Add basic auth
      httpHostHeader: ollama.mostarindustries.com
      # Or use Cloudflare Access (better)
  - service: http_status:404
```

### Option 2: Cloudflare Access (Free for 50 users)

1. Go to Cloudflare Dashboard → Zero Trust
2. Create an Access Application
3. Protect `ollama.mostarindustries.com`
4. Add authentication rules (email, Google, etc.)

### Option 3: IP Allowlist

In Cloudflare Dashboard:

1. **Firewall** → **Tools**
2. Create firewall rule:
   - **Field**: Hostname
   - **Operator**: equals
   - **Value**: `ollama.mostarindustries.com`
   - **Action**: Block (except for allowed IPs)

---

## 📊 Monitoring

### View Tunnel Metrics

```powershell
cloudflared tunnel info mostar-ollama
```

### Cloudflare Dashboard

- Analytics: <https://dash.cloudflare.com> → Analytics
- Logs: Zero Trust → Logs → Access

---

## 🐛 Troubleshooting

### Tunnel won't start

```powershell
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check tunnel config
cloudflared tunnel info mostar-ollama

# View logs
cloudflared tail
```

### DNS not resolving

```powershell
# Check DNS propagation
nslookup ollama.mostarindustries.com

# Force DNS update
cloudflared tunnel route dns mostar-ollama ollama.mostarindustries.com
```

### Connection refused

- Ensure Ollama is running: `ollama serve`
- Check Windows Firewall
- Verify `config.yml` has correct localhost port

---

## 🎯 Final Architecture

```
Supabase Edge Function (Cloud)
         ↓
https://ollama.mostarindustries.com
         ↓
Cloudflare Tunnel (Encrypted)
         ↓
Your Local Machine: localhost:11434
         ↓
Ollama (Mostar-AI Models)
```

---

## 📝 Quick Reference

**Start tunnel**: `cloudflared tunnel run mostar-ollama`  
**Stop tunnel**: `Ctrl+C` (or `Stop-Service cloudflared`)  
**View logs**: `cloudflared tail`  
**Test URL**: `https://ollama.mostarindustries.com/api/tags`  
**Config file**: `C:\Users\idona\.cloudflared\config.yml`

---

## 🔥 Next Steps

1. ✅ Run through Steps 1-8
2. ✅ Test the tunnel
3. ✅ Update Supabase secrets
4. ✅ Test chat from frontend
5. ✅ Set up authentication (optional but recommended)

---

**🔥 Àṣẹ! Your Ollama will be globally accessible! 🔥**
