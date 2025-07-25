// FILE: frontend/src/AccountInfo.js

import React from 'react';
import './AccountInfo.css'; 

function AccountInfo({ accountData }) {
  // Show a loading message if data hasn't arrived yet
  if (!accountData) {
    return <div className="account-info-container">Loading account data...</div>;
  }
  
  // Show an error message if the fetch failed
  if (accountData.error) {
    return <div className="account-info-container">{accountData.error}</div>;
  }

  // 2. Add the CSS classNames to the divs
  return (
    <div className="account-info-container">
      <h3>Account Overview</h3>
      <div className="account-info-details">
        <p><strong>Status:</strong> {accountData.status}</p>
        <p><strong>Account Number:</strong> {accountData.account_number}</p>
        <p><strong>Portfolio Value:</strong> ${accountData.portfolio_value}</p>
        <p><strong>Buying Power:</strong> ${accountData.buying_power}</p>
        <p><strong>Cash:</strong> ${accountData.cash}</p>
      </div>
    </div>
  );
}

export default AccountInfo;