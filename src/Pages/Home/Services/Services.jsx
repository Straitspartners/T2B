import React from "react";
import "./Services.css";

const Features = () => {
  return (
    <section id="services" className="features-section">
      <div className="features-container">
        <h2 className="features-title">
          Key Features of Our Migration
          <h2>
            {" "}
            <span className="highlight">Services</span>
          </h2>
        </h2>
        <div className="features-grid">
          {/* Data Migration Card */}
          <div className="feature-card">
            <div className="card-content">
              <div className="card-text">
                <div className="card-header">
                  <div className="card-number blue">1</div>
                  <h3 className="card-title">Data Migration</h3>
                </div>
                <ul className="feature-list">
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Complete transfer of chart of accounts, customer, vendors
                    and items
                  </li>
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Migration of historical transactions and financial
                    statements
                  </li>
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Preservation of audit trails and document attachments
                  </li>
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Data validation and integrity checks
                  </li>
                </ul>
                <button className="learn-more-btn blue">Learn More</button>
              </div>
              <div className="card-visual">
           <div className="overview-widget">
      <div className="widget-header">
        <div className="header-content">
          <div className="icon-container">
            <div className="widget-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="4" width="18" height="16" rx="2" stroke="white" strokeWidth="2"/>
                <path d="M3 8h18" stroke="white" strokeWidth="2"/>
                <path d="M8 12h8" stroke="white" strokeWidth="2"/>
                <path d="M8 16h6" stroke="white" strokeWidth="2"/>
              </svg>
            </div>
            <span className="widget-title">Overview</span>
          </div>
        </div>
      </div>
      <div className="widget-body">
      <div className="widget-content">
        
        <div className="data-section">
          <div className="data-label">Total Data's</div>
          <div className="data-value-container">
            <span className="data-value">12,500</span>
            <span className="data-subtitle">Data imported</span>
            <div className="percentage-badge">+20%</div>
          </div>
        </div>
        
        <div className="chart-section">
          <div className="chart-container">
            <div className="chart-bar" style={{ height: '45%' }}></div>
            <div className="chart-bar" style={{ height: '55%' }}></div>
            <div className="chart-bar" style={{ height: '70%' }}></div>
            <div className="chart-bar" style={{ height: '85%' }}></div>
            <div className="chart-bar active" style={{ height: '100%' }}></div>
            <div className="chart-bar" style={{ height: '75%' }}></div>
            <div className="chart-bar" style={{ height: '80%' }}></div>
          </div>
          
          <div className="chart-labels">
            <span>Sun</span>
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span>Sat</span>
          </div>
        </div>
      </div>
      </div>
    </div>
              </div>
            </div>
          </div>
          {/* Custom Configuration Card - Changed to Blue */}
          <div className="feature-card">
            <div className="card-content">
              <div className="card-visual " style={{justifyContent:"flex-start"}}>
                <div className="visual-widget">
                  <div className="widget-header">
                    <span className="widget-label">Configuration</span>
                    <div className="widget-icon blue">⚙️</div>
                  </div>
                  <div className="config-list">
                    <div className="config-item">
                      <span className="config-label">Tax Rates</span>
                      <div className="status-icon complete">✓</div>
                    </div>
                    <div className="config-item">
                      <span className="config-label">Currencies</span>
                      <div className="status-icon complete">✓</div>
                    </div>
                    <div className="config-item">
                      <span className="config-label">Templates</span>
                      <div className="status-icon processing">⟳</div>
                    </div>
                    <div className="config-item">
                      <span className="config-label">Integrations</span>
                      <div className="status-icon pending"></div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="card-text">
                <div className="card-header">
                  <div className="card-number blue " >4</div>
                  <h3 className="card-title">Custom Configuration</h3>
                </div>
                <ul className="feature-list">
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Custom setup Zoho Books to match your business processes
                  </li>
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Configuration of tax rates, currencies, and financial years
                  </li>
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Setup of custom fields, templates, and automation rules
                  </li>
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Integration with other business systems and banking
                  </li>
                </ul>
                <button className="learn-more-btn blue">Learn More</button>
              </div>
            </div>
          </div>
        

          {/* Training & Support Card - Changed to Blue */}
          <div className="feature-card">
            <div className="card-content">
              <div className="card-text">
                <div className="card-header">
                  <div className="card-number blue">3</div>
                  <h3 className="card-title">Training & Support</h3>
                </div>
                <ul className="feature-list">
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Comprehensive training sessions for your accounting team
                  </li>
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Customized documentation and process guides
                  </li>
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    30-day post-migration support for troubleshooting
                  </li>
                  <li className="feature-item">
                    <span className="check-icon blue">✓</span>
                    Ongoing maintenance and support packages available
                  </li>
                </ul>
                <button className="learn-more-btn blue">Learn More</button>
              </div>
              <div className="card-visual ">
                <div className="visual-widget">
                  <div className="widget-header">
                    <span className="widget-label">Training Progress</span>
                    <div className="widget-icon blue">📚</div>
                  </div>
                  <div className="progress-section">
                    <div className="progress-header">
                      <span>Data Migration</span>
                      <span>100%</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill purple"
                        style={{ width: "100%" }}
                      ></div>
                    </div>
                  </div>
                  <div className="progress-section">
                    <div className="progress-header">
                      <span>System Setup</span>
                      <span>85%</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill purple"
                        style={{ width: "85%" }}
                      ></div>
                    </div>
                  </div>
                  <div className="progress-section">
                    <div className="progress-header">
                      <span>User Training</span>
                      <span>60%</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill purple"
                        style={{ width: "60%" }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;
