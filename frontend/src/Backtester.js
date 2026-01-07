
import React, { useState } from 'react';
import './Backtester.css';
import {LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer} from 'recharts';
function Backtester({symbol, setSymbol}) {
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [liveStatus, setLiveStatus] = useState('');
  const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
  const handleRunBacktest = () => {
    setLoading(true);
    setResult(null);

    fetch(`${API_URL}/api/backtest/${symbol}`, {method: 'POST'})
      
      .then(async (response) => {
        // This block checks if the server responded with an error
        const data = await response.json();

        if (!response.ok) {
          
          throw new Error(data.detail || 'Failed to run backtest.');
        }
        return data;
      })
      .then(data => {
        
        setResult(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching backtest data:', error);
        setResult({ error: 'Make sure the entered symbol is valid. If it is, please wait 20–30 seconds for the Render backend server to wake up (cold start).' });
        setLoading(false);
      });
  };
  const handleStartLive = () => {
    setLiveStatus(`Starting live trading for ${symbol}...`);
    fetch(`${API_URL}/api/livetrade/start/${symbol}`, { method: 'POST' })
      .then(async (response) => {
          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.detail || 'Failed to start.');
          }
          return data;
      })
      
      .then(data => setLiveStatus(data.message || data.detail))
      .catch((error) => setLiveStatus(`Error: ${error.message}`));
  };
  const handleStopLive = () => {
    setLiveStatus(`Stopping live trading for ${symbol}...`);
    fetch(`${API_URL}/api/livetrade/stop/${symbol}`, { method: 'POST' })
      .then(response => response.json())
      .then(data => setLiveStatus(data.message || data.detail))
      .catch(() => setLiveStatus('Failed to stop live trading.'));
  };
  

return (
    <div className="backtester-container">
      
      <div className="backtester-left">
        <div className="backtester-section">
          <h3>Run a Backtest</h3>
          <button onClick={handleRunBacktest} disabled={!symbol || loading}>
            {loading ? 'Running...' : 'Run Backtest'}
          </button>
        </div>
        <div className="backtester-section">
          <h3>Live Paper Trading</h3>
          <button onClick={handleStartLive} disabled={!symbol}>Start Live</button>
          <button onClick={handleStopLive} disabled={!symbol}>Stop Live</button>
          {liveStatus && <p className="status-text">Status: {liveStatus}</p>}
        </div>
      </div>

      
      {(loading || result) && (
        <div className="backtester-right">
          {loading && <p>Running backtest...</p>}
          
          {result && !result.error && (
            <div className="result-block">
              <h4>Backtest Result for: {result.symbol}</h4>
              <p><strong>Starting Value:</strong> ${result.starting_value?.toLocaleString()}</p>
              <p><strong>Final Value:</strong> ${result.final_value?.toLocaleString()}</p>
              <p><strong>Profit/Loss:</strong> ${(result.final_value - result.starting_value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
              
              {result.chart_data && (
                <div className="backtester-chart">
                  <ResponsiveContainer> // it forces the chart to stretch to fill the parent div automatically.
                    <LineChart data={result.chart_data}>
                      <CartesianGrid strokeDasharray="3 3" /> // Draws the faint grid lines behind the graph.
                      <XAxis dataKey="timestamp" />
                      <YAxis domain={['auto', 'auto']} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="close" stroke="#4ac26c" name="Close Price" dot={false} /> // no dots, forms a line
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {result?.error && (
            <div className="error-text">{result.error}</div>
          )}
        </div>
      )}
    </div>
  );

}

export default Backtester;
