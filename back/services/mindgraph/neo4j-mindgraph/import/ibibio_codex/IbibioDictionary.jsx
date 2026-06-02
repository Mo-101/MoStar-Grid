import React, { useState, useEffect } from 'react';
import './IbibioDictionary.css';

const API_BASE = 'http://localhost:5000/api';

function IbibioDictionary() {
  const [words, setWords] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [currentAudio, setCurrentAudio] = useState(null);

  useEffect(() => {
    fetchStats();
    fetchWords();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchWords = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/words`);
      const data = await res.json();
      setWords(data.words || []);
    } catch (error) {
      console.error('Error fetching words:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchWords = async () => {
    if (!searchQuery.trim()) {
      fetchWords();
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/words/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      setWords(data.words || []);
    } catch (error) {
      console.error('Error searching words:', error);
    } finally {
      setLoading(false);
    }
  };

  const playAudio = (audioFile, word) => {
    if (currentAudio) {
      currentAudio.pause();
    }

    if (audioFile) {
      const audio = new Audio(`http://localhost:5000/api/audio/${audioFile}`);
      audio.play();
      setCurrentAudio(audio);
    } else {
      alert(`No audio available for "${word}"`);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchWords();
    }
  };

  return (
    <div className="ibibio-dictionary">
      <header className="header">
        <h1>🔥 Iko Ikang</h1>
        <p className="subtitle">Voice of Flame - Ibibio Dictionary</p>
        {stats && (
          <div className="stats">
            <span>{stats.total_words} words</span>
            <span>{stats.speakers?.length} speakers</span>
            <span>{stats.total_entities} entities</span>
            <span>{stats.total_odu} Odù</span>
          </div>
        )}
      </header>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search in English (e.g., 'hello', 'one', 'water')"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          className="search-input"
        />
        <button onClick={searchWords} className="search-button">
          Search
        </button>
        <button onClick={fetchWords} className="clear-button">
          Show All
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <div className="words-grid">
          {words.map((word, index) => (
            <div key={index} className="word-card">
              <div className="word-ibibio">{word.word || 'N/A'}</div>
              <div className="word-english">{word.english || 'N/A'}</div>
              <div className="word-speaker">{word.speaker || 'Unknown'}</div>
              <button
                onClick={() => playAudio(word.audio_file, word.word)}
                className="play-button"
                disabled={!word.audio_file}
              >
                {word.audio_file ? '▶️ Play' : '🔇 No Audio'}
              </button>
            </div>
          ))}
        </div>
      )}

      {words.length === 0 && !loading && (
        <div className="no-results">
          No words found. Try a different search term.
        </div>
      )}
    </div>
  );
}

export default IbibioDictionary;
