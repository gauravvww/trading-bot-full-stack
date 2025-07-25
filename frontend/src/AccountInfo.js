

import React from 'react';
import './AccountInfo.css'; 

function AccountInfo({ accountData }) {

  if (!accountData) {
    return <div className="account-info-container">Loading account data...</div>;
  }
  

  if (accountData.error) {
    return <div className="account-info-container">{accountData.error}</div>;
  }


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