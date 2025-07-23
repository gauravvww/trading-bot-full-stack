import React from 'react';

function AccountInfo({accountData}){

     if(!accountData){
        return <div>Loading account data...</div>;
    }
    if(accountData.error){
        return <div style =  {{color: 'red'}} >Error: {accountData.error}</div>;

    }
   
    return (
    <div style={{ border: '1px solid grey', padding: '15px', borderRadius: '8px', marginTop: '20px' }}>
      <h3>Account Details</h3>
      <p><strong>Status:</strong> {accountData.status}</p>
      <p><strong>Account Number:</strong> {accountData.account_number}</p>
      <p><strong>Portfolio Value:</strong> ${parseFloat(accountData.portfolio_value).toLocaleString()}</p>
      <p><strong>Buying Power:</strong> ${parseFloat(accountData.buying_power).toLocaleString()}</p>
      <p><strong>Cash:</strong> ${parseFloat(accountData.cash).toLocaleString()}</p>
    </div>
  );
}

export default AccountInfo;
