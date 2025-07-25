// FILE: frontend/src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import AccountInfo from './AccountInfo.js';
import Backtester from './Backtester.js';

function App() {
  const [accountInfo, setAccountInfo] = useState(null);
  const [symbol, setSymbol] = useState(''); // Symbol state is now here

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/account')
      .then(response => response.json())
      .then(data => {
        setAccountInfo(data);
      })
      .catch(error => {
        console.error('Error fetching account data:', error);
        setAccountInfo({ error: 'Could not connect to backend' });
      });
  }, []);

  return (
    <div className="app-container">
      <header className="navbar">
        <h2>AlgoBot</h2>
      </header>
      <h1>Trading Bot Dashboard</h1>
      
      {/* 1. Account Overview */}
      <section>
        <AccountInfo accountData={accountInfo} />
      </section>

      {/* 2. Shared Symbol Input */}
      <div className="symbol-input-section">
        <h3>Enter Stock Symbol</h3>
        <input
          type="text"
          value={symbol}
          onChange={e => setSymbol(e.target.value.toUpperCase())}
          placeholder="Enter stock symbol (e.g., AAPL, TSLA, MSFT)"
        />
      </div>
      
      {/* 3. Backtester / Live Trading Controls */}
      <section>
        <Backtester symbol={symbol} setSymbol={setSymbol} />
      </section>
    </div>
  );
}

export default App;