
import React, { useState } from 'react';

function Backtester() {
  const [symbol, setSymbol] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRunBacktest = () => {
    setLoading(true);
    setResult(null);

    fetch(`http://127.0.0.1:8000/api/backtest/${symbol}`)
      .then(response => response.json())
      .then(data => {
        setResult(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching backtest data:', error);
        setResult({ error: 'Failed to run backtest.' });
        setLoading(false);
      });
  };

  return (
    <div style={{width: '300px', border: '1px solid grey', padding: '15px', borderRadius: '8px', marginTop: '20px' }}>
      <h3>Run a Backtest</h3>
      <div>
        <input
       style = {{width: '300px'}} 
          type="text"
          value={symbol}
          onChange={e => setSymbol(e.target.value.toUpperCase())}
          placeholder="Enter stock symbol (e.g., AAPL)"
        />
        <button onClick={handleRunBacktest} disabled={loading}>
          {loading ? 'Running...' : 'Run Backtest'}
        </button>
      </div>

      {result && (
        <div style={{ marginTop: '15px' }}>
         
          {result.error ? (
            <p style={{ color: 'red' }}>{result.error}</p>
          ) : (
            <>
             
              <h4>Backtest Result for: {result.symbol}</h4>
              <p><strong>Starting Value:</strong> ${result.starting_value?.toLocaleString()}</p>
              <p><strong>Final Value:</strong> ${result.final_value?.toLocaleString()}</p>
              <p><strong>Profit/Loss:</strong> ${ (result.final_value - result.starting_value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }</p>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default Backtester;