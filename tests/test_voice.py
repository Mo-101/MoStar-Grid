import pytest
import os
import asyncio
from pathlib import Path
from core_engine.voice_integration import hash_text, speak_async

def test_hash_text():
    text = "Hello MoStar"
    h1 = hash_text(text)
    h2 = hash_text(text)
    assert h1 == h2
    assert len(h1) == 32 # md5 hexdigest

@pytest.mark.asyncio
async def test_speak_async_caching():
    text = "This is a test of the MoStar voice caching system."
    # Use a specific cache dir for test if possible, but for now use default
    cache_dir = Path("audio_cache")
    
    # First call (generates file)
    file_path = await speak_async(text)
    assert os.path.exists(file_path)
    
    # Second call (should be from cache)
    file_path_cached = await speak_async(text)
    assert file_path == file_path_cached
    
    # Cleanup if needed (optional)
    # os.remove(file_path)
