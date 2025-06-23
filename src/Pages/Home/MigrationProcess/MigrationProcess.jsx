import React from 'react';
import './MigrationProcess.css';


const MigrationProcess = () => (
  <section id="MigrationProcess" className="process-section">
    <h2 className="features-title"> Our <span className="highlight"> Migration </span> Process </h2>
    <div className="steps">  
      <div className="step">
        <div className="step-overlay">
          <div className="step-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm5-18v4h3V3h-3z" fill="white"/>
            </svg>
          </div>
          <div className="step-title">Assessment</div>
          <div className="step-description">
            We analyze your current Tally setup and data structure.
          </div>
        </div>
      </div>
      
      <div className="step">
        <div className="step-overlay">
          <div className="step-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="white"/>
            </svg>
          </div>
          <div className="step-title">Preparation</div>
          <div className="step-description">
            We clean, format and validate data to ensure accuracy before migration.
          </div>
        </div>
      </div>
      
      <div className="step">
        <div className="step-overlay">
          <div className="step-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="white"/>
            </svg>
          </div>
          <div className="step-title">Planning</div>
          <div className="step-description">
            We craft a tailored migration strategy and milestones for a smooth transition.
          </div>
        </div>
      </div>
      
      <div className="step">
        <div className="step-overlay">
          <div className="step-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-5 2.5c0 .83-.67 1.5-1.5 1.5S12 7.33 12 6.5 12.67 5 13.5 5s1.5.67 1.5 1.5zm-4 0C11 7.33 10.33 8 9.5 8S8 7.33 8 6.5 8.67 5 9.5 5s1.5.67 1.5 1.5zM5 17.5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5S7.33 19 6.5 19 5 18.33 5 17.5zm3.5-3.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm5 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z" fill="white"/>
            </svg>
          </div>
          <div className="step-title">Migration Services</div>
          <div className="step-description">
            We execute the migration to Zoho Books with minimal disruption to operations
          </div>
        </div>
      </div>
      
      <div className="step">
        <div className="step-overlay">
          <div className="step-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" fill="white"/>
            </svg>
          </div>
          <div className="step-title">Support</div>
          <div className="step-description">
            We provide training and ongoing assistance
          </div>
        </div>
      </div>
    </div>
  </section>
);

export default MigrationProcess;