
import './FAQ.css';

import React, { useState } from 'react';


const ZohoBooksInterface = () => {
  const [activeTab, setActiveTab] = useState('Daily');

  const migrationData = {
    Daily: {
      tallyImported: 500000,
      mappedToZoho: 495000,
      pendingAdjustments: 2000,
      completionRate: 96
    },
    Weekly: {
      tallyImported: 3500000,
      mappedToZoho: 3465000,
      pendingAdjustments: 14000,
      completionRate: 98
    },
    Monthly: {
      tallyImported: 15000000,
      mappedToZoho: 14850000,
      pendingAdjustments: 60000,
      completionRate: 99
    },
    Status: {
      tallyImported: 25000000,
      mappedToZoho: 24750000,
      pendingAdjustments: 100000,
      completionRate: 99
    }
  };

  const migrationHistory = [
    {
      id: 1,
      company: 'ABC Enterprises',
      initials: 'ABC',
      date: 'May 2024',
      amount: 1500000,
      type: 'positive'
    },
    {
      id: 2,
      company: 'XYZ Ltd.',
      initials: 'XYZ',
      date: 'April 2024',
      amount: -500,
      type: 'negative'
    }
  ];

  const formatCurrency = (amount) => {
    if (amount >= 10000000) {
      return `₹${(amount / 10000000).toFixed(1).replace('.0', '')},00,00,000`;
    } else if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(1).replace('.0', '')},95,000`;
    } else if (amount >= 1000) {
      return `₹${Math.floor(amount / 1000)},000`;
    }
    return `₹${amount.toLocaleString()}`;
  };

  const formatHistoryAmount = (amount) => {
    if (amount > 0) {
      return `+ ${Math.floor(amount / 100000)},50,000`;
    }
    return `-500`;
  };

  return (
    <div className="zoho-container">
      <div className="content-wrapper">
        <div className="left-section">
          <h1 className="main-title">
            Ready to Streamline Your Zoho Books Migration?
          </h1>
          <p className="subtitle">
            Transform your financial management with our advanced SaaS platform designed 
            for seamless migration to Zoho Books. Begin enhancing your financial processes 
            today!
          </p>
          <button className='learn-more-btn'>
            Schedule a Demo
          </button>
        </div>

        <div className="right-section">
          <div className="dashboard-card">
            {/* Tab Container */}
            <div className="tab-container">
              {['Daily', 'Weekly', 'Monthly', 'Status'].map((tab) => (
                <button
                  key={tab}
                  className={`tab-button ${activeTab === tab ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Migration Data Rows */}
            <div className="data-rows">
              <div className="data-row">
                <span className="data-label">Tally Data Imported</span>
                <span className="data-value">₹5,00,000</span>
              </div>
              
              <div className="data-row">
                <span className="data-label">Mapped to Zoho Books</span>
                <span className="data-value">₹4,95,000</span>
              </div>
              
              <div className="data-row">
                <span className="data-label">Pending Adjustments</span>
                <span className="data-value">2,000</span>
              </div>
              
              <div className="data-row">
                <span className="data-label">Status</span>
                <span className="data-value status-complete">96% Complete</span>
              </div>
            </div>

            {/* Migration History */}
            <div className="history-section">
              <h3 className="history-title">Migration History</h3>
              
              <div className="history-item">
                <div className="company-avatar abc-avatar">ABC</div>
                <div className="company-info">
                  <div className="company-name">ABC Enterprises</div>
                  <div className="company-date">May 2024</div>
                </div>
                <div className="amount-positive">+ 1,50,000</div>
              </div>
              
              <div className="history-item">
                <div className="company-avatar xyz-avatar">XYZ</div>
                <div className="company-info">
                  <div className="company-name">XYZ Ltd.</div>
                  <div className="company-date">April 2024</div>
                </div>
                <div className="amount-negative">-500</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ZohoBooksInterface;