# 🔥 IKO IKANG - IBIBIO TTS SYSTEM
## Voice of Flame - Complete Setup Guide

---

## WHAT YOU GOT

**Backend**: Flask API (Python)
**Frontend**: React component
**Database**: Neo4j (already running with 12,087 nodes)
**Audio**: 180 MP3 files

---

## STEP 1: START THE FLASK API (2 minutes)

### Install Dependencies

```bash
cd "C:\Users\AI\Documents\MoStar\Mo Docs"
pip install flask flask-cors neo4j --break-system-packages
```

### Update Password in API

Open `ibibio_tts_api.py` and change line 14:

```python
NEO4J_PASSWORD = "YOUR_PASSWORD_HERE"  # Replace with your Neo4j password
```

### Run the API

```bash
python ibibio_tts_api.py
```

**Expected Output:**
```
🔥 Iko Ikang - Voice of Flame API Starting...
📊 Neo4j: bolt://localhost:7687
🎵 Audio: C:\Users\AI\Documents\MoStar\Mo Docs\neo4j-community-2025.10.1\import\Ibibio_audio
🌐 Server: http://localhost:5000
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

**Test it:**
Open browser: http://localhost:5000/health

Should see: `{"status": "online", "message": "Iko Ikang - Voice of Flame"}`

---

## STEP 2: ADD REACT COMPONENT (5 minutes)

### If you have an existing React app:

1. Copy `IbibioDictionary.jsx` to your `src/components/` folder
2. Copy `IbibioDictionary.css` to your `src/components/` folder
3. Import in your `App.js`:

```jsx
import IbibioDictionary from './components/IbibioDictionary';

function App() {
  return (
    <div>
      <IbibioDictionary />
    </div>
  );
}
```

### If you DON'T have a React app yet:

Create one:

```bash
npx create-react-app ibibio-tts
cd ibibio-tts
```

Then copy the files and modify `src/App.js` as shown above.

Start React:
```bash
npm start
```

---

## STEP 3: TEST IT (1 minute)

1. Make sure Neo4j is running (localhost:7474)
2. Make sure Flask API is running (localhost:5000)
3. Open React app (localhost:3000)

You should see:
- Header: "🔥 Iko Ikang - Voice of Flame"
- Stats: "196 words, 2 speakers, 13 entities, 256 Odù"
- Search bar
- Grid of Ibibio words
- Click "▶️ Play" to hear native pronunciation

---

## API ENDPOINTS

### GET /health
Check if API is running

### GET /api/words
Get all Ibibio words (up to 200)

### GET /api/words/search?q=hello
Search words by English meaning

### GET /api/words/numbers
Get Ibibio numbers 1-10

### GET /api/audio/{filename}
Stream audio file

### GET /api/word/{word}
Get details for specific Ibibio word

### GET /api/stats
Get database statistics

---

## EXAMPLE SEARCHES

Try searching for:
- `one` - Numbers
- `hello` - Greetings
- `water` - Common words
- `mother` - Family terms
- `grind` - Actions

---

## WHAT'S NEXT

After this works, we can:
1. Add Mo entity voice integration
2. Connect to REMOSTAR consciousness
3. Build DeepCAL symbolic reasoning interface
4. Create voice chat with Ibibio responses
5. Deploy to production

---

## TROUBLESHOOTING

**"Connection refused to Neo4j"**
- Make sure Neo4j Desktop is running
- Check password in `ibibio_tts_api.py`

**"Audio file not found"**
- Verify audio files are in: `C:\Users\AI\Documents\MoStar\Mo Docs\neo4j-community-2025.10.1\import\Ibibio_audio`
- Check file permissions

**"CORS error"**
- Flask CORS is enabled, should work
- If still issues, check browser console

**"No words showing"**
- Check Flask API logs for errors
- Test endpoint: http://localhost:5000/api/words
- Verify Neo4j has IbibioWord nodes

---

## FILES CREATED

1. `ibibio_tts_api.py` - Flask backend API
2. `IbibioDictionary.jsx` - React component
3. `IbibioDictionary.css` - Styling
4. `requirements.txt` - Python dependencies

---

**IKO IKANG!** 🔥

The Voice of Flame speaks.
