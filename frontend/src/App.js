import React, { useState, useEffect } from 'react';
import './App.css';
import AccountInfo from './AccountInfo';
import Backtester from './Backtester'; 

function App() {
  const [accountInfo, setAccountInfo] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/account')
    .then(response => response.json()) 
    .then(data => {
      setAccountInfo(data);
    })
    .catch(error => {
      console.error('Error fetching account Data: ', error);
      setAccountInfo({error: 'Could not connect to backend'});
    });
  }, []);

  return (
    
    <div className="App">
        <header className="navbar">
         <h2> AlgoBot</h2>
        </header>

        <h1>Trading Bot Dashboard</h1>
        <section>
        <AccountInfo accountData = {accountInfo}></AccountInfo>
        </section>
        <section>
        <Backtester />
        </section>
      
       </div>
  );
}
export default App;