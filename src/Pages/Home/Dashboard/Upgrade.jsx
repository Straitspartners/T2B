import React from 'react';
import Sidebar from '../../../components/Sidebar';
import './Upgrade.css';
import { Bell, User, Star } from 'lucide-react';

function Upgrade() {
  return (
    
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main className="upgrade-main">
      <div className="header">
          <div className="header-left">
            <h1>Dashboard</h1>
            <p>Monitor and manage your entire data migration process from a single dashboard</p>
          </div>
          <div className="header-right">
            <Bell className="notification-icon" />
            <div className="user-profile">
              <User className="user-icon" />
              <span>{JSON.parse(localStorage.getItem("userData") || '{}')?.name || localStorage.getItem("userName") || "User"}</span>
            </div>
          </div>
        </div>

        <div className="plan-toggle">
          <button className="toggle-btn active">Real-time and One-time</button>
        </div>

        <div className="plans-container">
          {/* Free Plan */}
          <div className="plan-card">
            <div className="plan-header">
              <div className="plan-icon free-icon">
                <Star className="star-icon" />
              </div>
              <h3>Free Plan</h3>
            </div>
            <p className="plan-description">
              Perfect for small businesses and first-time users. 
              Start migrating your Tally data to Zoho Books 
              with ease — at zero cost!
            </p>
            
            <div className="features-list">
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Push up to 500 records per day</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Basic Tally to Zoho Books migration</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Standard Data Mapping</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Email Support (5 tickets/month)</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Access to Community Forum</span>
              </div>
              <div className="feature-item limitation">
                <span className="cross-icon">✗</span>
                <span>No priority support</span>
              </div>
              <div className="feature-item limitation">
                <span className="cross-icon">✗</span>
                <span>No advanced automation</span>
              </div>
              <div className="feature-item limitation">
                <span className="cross-icon">✗</span>
                <span>No team collaboration</span>
              </div>
            </div>

            <button className="plan-button secondary">Get Started</button>
            
            <div className="plan-note">
              <span className="info-icon">💡</span>
              <span>Great for testing and small, low-volume migrations</span>
            </div>
          </div>

          {/* Premium Plan */}
          <div className="plan-card premium">
            <div className="plan-header">
              <div className="plan-icon premium-icon">
              <Star className="star-icon" />
              </div>
              <h3>Premium Plan</h3>
            </div>
            <div className="plan-price">
              <span className="currency">₹</span>
              <span className="amount">999</span>
              <span className="period">/-</span>
              <span className="currency-code">INR</span>
            </div>
            <p className="plan-description">
              Built for large businesses and high-volume migrations.
            </p>
            
            <div className="features-list">
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Unlimited daily data push</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Dedicated Migration Manager</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Custom Data Mapping & Validation</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Real-Time Sync</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Advanced Automation Workflows</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Integration Support (Custom APIs)</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Role-Based Access for up to 20 users</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Dedicated Account Manager</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>24/7 Priority Support</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Compliance & Audit Reports</span>
              </div>
            </div>

            <button className="plan-button primary">Go Premium</button>
          </div>

          {/* Elite Plan */}
          <div className="plan-card">
            <div className="plan-header">
              <div className="plan-icon elite-icon">
           <Star className="star-icon" />
              </div>
              <h3>Elite Plan</h3>
            </div>
            <div className="plan-price">
              <span className="currency">₹</span>
              <span className="amount">599</span>
              <span className="period">/-</span>
              <span className="currency-code">INR</span>
            </div>
            <p className="plan-description">
              Great for growing businesses with big data needs.
            </p>
            
            <div className="features-list">
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Push up to 5,000 records per day</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Priority Data Migration</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Advanced Data Mapping Rules</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Auto-Schedule Syncs</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Daily Backup & Restore</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Email & Chat Support (Priority)</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Role-Based Access for up to 5 users</span>
              </div>
              <div className="feature-item">
                <span className="check-icon2">✓</span>
                <span>Error Reports & Logs</span>
              </div>
            </div>

            <button className="plan-button secondary">Upgrade to Elite</button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Upgrade;
