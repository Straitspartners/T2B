import React, { useState } from 'react';
import './Setup.css';
import axios from 'axios';


const SyncDataFlow = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState('');

const [formData, setFormData] = useState({
  client_id: '',
  client_secret: '',
  access_token: '',
  refresh_token: '',
  organization_id: ''
});

  const steps = [
    {
      title: "Connect Zoho Books Account",
      subtitle: "Securely connect your Zoho Books account to begin the migration process from Tally. Your credentials are encrypted and never stored.",
      sections: [
        {
          title: "How to get Zoho Books API Credentials",
          subsections: [
            { 
              title: "1. Client ID & Client Secret",
              steps: [
                "Go to Zoho API Console.",
                "Create a new client (choose \"Server-based\" client).",
                "Copy the Client ID and Client Secret."
              ]
            },
            { 
              title: "2. Access Token & Refresh Token",
              steps: [
                "Use Postman or a token generation tool (add link).",
                "Pass the client credentials and authorization code.",
                "Zoho will return access_token and refresh_token."
              ]
            },
            { 
              title: "3. Organization ID",
              steps: [
                "Login to Zoho Books.",
                "Go to Settings → Organization Profile.",
                "You'll find Organization ID in the URL or API response."
              ]
            }
          ]
        }
      ],
      formFields: [
        { label: "Client ID", placeholder: "Enter your Client ID" },
        { label: "Client Secret", placeholder: "Enter your Client ID" },
        { label: "Access Token", placeholder: "Enter your Access Token" },
        { label: "Refresh Token", placeholder: "Enter your Refresh Token" },
        { label: "Organization ID", placeholder: "Enter" }
      ]
    },
    {
      title: "Connect Zoho Books API Credentials",
      subtitle: "Securely connect your Zoho Books account to begin the migration process from Tally. Your credentials are encrypted and never stored.",
      sections: [
        {
          title: "How to get Zoho Books API Credentials",
          subsections: [
            { 
              title: "1. Client ID & Client Secret",
              steps: [
                "Go to Zoho API Console.",
                "Create a new client (choose \"Server-based\" client).",
                "Copy the Client ID and Client Secret."
              ]
            },
            { 
              title: "2. Access Token & Refresh Token",
              steps: [
                "Use Postman or a token generation tool (add link).",
                "Pass the client credentials and authorization code.",
                "Zoho will return access_token and refresh_token."
              ]
            },
            { 
              title: "3. Organization ID",
              steps: [
                "Login to Zoho Books.",
                "Go to Settings → Organization Profile.",
                "You'll find Organization ID in the URL or API response."
              ]
            }
          ]
        }
      ],
    formFields: [
  { label: "Client ID", name: "client_id", placeholder: "Enter your Client ID" },
  { label: "Client Secret", name: "client_secret", placeholder: "Enter your Client Secret" },
  { label: "Access Token", name: "access_token", placeholder: "Enter your Access Token" },
  { label: "Refresh Token", name: "refresh_token", placeholder: "Enter your Refresh Token" },
  { label: "Organization ID", name: "organization_id", placeholder: "Enter your Organization ID" }
]

    },
    {
      title: "Connect Tally Account",
      subtitle: "Ready to Migrate? Connect to continue the migration process from Tally to Zoho Books.",
      sections: [
        {
          title: "How to Connect Tally with Zoho Books",
          subsections: [
            { 
              title: "Step 1: Port Data to Zoho",
              steps: [
                "Make sure to install and access the connector from the Zoho Books dashboard."
              ]
            },
            { 
              title: "Step 2: Run the Sync Agent",
              steps: [
                "Download and install the Sync Agent on the system where TallyPrime is running.",
                "Configure the Sync Agent with your Zoho Books credentials.",
                "Start the Sync Agent."
              ]
            },
            { 
              title: "Step 3: Configure Tally",
              steps: [
                "Open TallyPrime.",
                "Configure TallyPrime to communicate with the Sync Agent.",
                "Verify the connection."
              ]
            }
          ]
        }
      ],
      formFields: []
    }
  ];

  const stepTitles = ["Zoho Books Integration", "Tally Integration", "SyncSonic Dashboard"];

const handleNext = async () => {
  if (currentStep === 0) {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(
        'https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/connect-zoho/',
        formData,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      console.log('Success:', response.data);
      setCompletedSteps([...completedSteps, currentStep]);
      setCurrentStep(currentStep + 1);
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to connect');
      console.error(err);
    } finally {
      setLoading(false);
    }
  } else {
    setCompletedSteps([...completedSteps, currentStep]);
    setCurrentStep(currentStep + 1);
  }
};


  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const StepIndicator = ({ stepIndex, isActive, isCompleted }) => (
    <div className="step-indicator">
      <div className={`step-circle ${isCompleted ? 'completed' : isActive ? 'active' : 'inactive'}`}>
        {stepIndex + 1}
      </div>
      <div className="step-label">
        {stepTitles[stepIndex]}
      </div>
      {stepIndex < steps.length - 1 && (
        <div className={`step-line ${completedSteps.includes(stepIndex) ? 'completed' : 'inactive'}`} />
      )}
    </div>
  );

  const currentStepData = steps[currentStep];

  return (
    <div className="sync-data-container">
      <div className="sync-data-wrapper">
        {/* Header */}
        <div className="header">
          <h1 className="main-title">Sync Sonic</h1>
          
          {/* Step Indicators */}
          <div className="step-indicators">
            {steps.map((_, index) => (
              <StepIndicator 
                key={index}
                stepIndex={index}
                isActive={index === currentStep}
                isCompleted={completedSteps.includes(index)}
              />
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="main-content">
          <div className="content-header">
            <h2 className="step-title">{currentStepData.title}</h2>
            <p className="step-subtitle">{currentStepData.subtitle}</p>
          </div>

          <div className="content-grid">
            {/* Instructions Section */}
            <div className="instructions-section">
              {currentStepData.sections.map((section, sectionIndex) => (
                <div key={sectionIndex} className="section">
                  <h3 className="section-title">{section.title}</h3>
                  
                  {section.subsections && (
                    <div className="subsections">
                      {section.subsections.map((subsection, subIndex) => (
                        <div key={subIndex} className="subsection">
                          <h4 className="subsection-title">{subsection.title}</h4>
                          {subsection.steps && (
                            <ul className="subsection-steps">
                              {subsection.steps.map((step, stepIndex) => (
                                <li key={stepIndex} className="subsection-step">{step}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                       {currentStep < 2 && (
                <div className="help-guide">
                  <button className="help-guide-button">View Detailed Help Guide</button>
                </div>
              )}
                    </div>
                  )}
                </div>
              ))}
              
             
            </div>

            {/* Form Section */}
            <div className="form-section">
              {currentStepData.formFields && currentStepData.formFields.length > 0 && (
                <div className="form-container">
                  <h3 className="form-title">Enter Zoho Books API Credentials :</h3>
                  {currentStepData.formFields.map((field, fieldIndex) => (
                    <div key={fieldIndex} className="form-field">
                      <label className="field-label">{field.label} :</label>
                      <input
  type="text"
  className="field-input"
  placeholder={field.placeholder}
  value={formData[field.name]}
  onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
/>

                    </div>
                  ))}
                  <div className="form-actions">
                    <button onClick={handleNext} className="connect-button">Connect & Proceed</button>
                  </div>
                </div>
              )}
              
              {currentStep === 2 && (
                <div className="completion-section">
                  <div className="completion-content">
                    <h3 className="completion-title">Step 3: Port Data to Zoho</h3>
                    <p className="completion-text">Make sure to install and access the connector from the Zoho Books dashboard.</p>
                    <p className="completion-text">Port</p>
                    <p className="completion-text">Note: Ensure port is valid and accessible.</p>
                    <button className="complete-setup-button">Complete Setup</button>
                  </div>
                </div>
              )}
              
            </div>
            
          </div>
            <div className="navigation">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className={`nav-button back-button ${currentStep === 0 ? 'disabled' : ''}`}
            >
              Back
            </button>

            <div className="step-counter">
              Step {currentStep + 1} of {steps.length}
            </div>

            <button
              onClick={handleNext}
              disabled={currentStep === steps.length - 1}
              className={`nav-button continue-button ${currentStep === steps.length - 1 ? 'complete' : ''}`}
            >
              {currentStep === steps.length - 1 ? 'Complete' : 'Continue'}
            </button>
          </div>
        </div>
        
      </div>
      {error && <div className="error-message">{error}</div>}
{loading && <div className="loading-message">Connecting to Zoho...</div>}

    </div>
  );
};

export default SyncDataFlow;