import React, { useState } from 'react';
import './Setup.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
const SyncDataFlow = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [snackbarAlert, setSnackbarAlert] = useState({ show: false, message: '', type: 'error' });

  // Form data only for step 0 (Zoho Books Integration)
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
    },
    {
      title: "Setup Complete!",
      subtitle: "Your Zoho Books and Tally integration has been successfully configured.",
      sections: [
        {
          title: "What's Next?",
          subsections: [
            { 
              title: "Access Your Dashboard",
              steps: [
                "Your integration is now ready to use.",
                "You can now access all features from your SyncSonic dashboard.",
                "Monitor your data synchronization in real-time."
              ]
            }
          ]
        }
      ],
      formFields: []
    }
  ];

  const stepTitles = ["Zoho Books Integration", "Tally Integration", "SyncSonic Dashboard"];

  // Snackbar alert function
  const showSnackbarAlert = (message, type = 'error') => {
    setSnackbarAlert({ show: true, message, type });
    setTimeout(() => {
      setSnackbarAlert({ show: false, message: '', type: 'error' });
    }, 8000); // Auto-hide after 8 seconds
  };

  const hideSnackbarAlert = () => {
    setSnackbarAlert({ show: false, message: '', type: 'error' });
  };

  // Handle form field changes for Zoho Books step
  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleNext = async () => {
    if (currentStep === 0) {
      // Validate required fields
      const requiredFields = ['client_id', 'client_secret', 'access_token', 'refresh_token', 'organization_id'];
      const emptyFields = requiredFields.filter(field => !formData[field]?.trim());
      
      if (emptyFields.length > 0) {
       showSnackbarAlert(`Please fill in the following required fields:\n${emptyFields.join(', ')}`);
return;
        return;
      }

      // API call for Zoho Books integration
      setLoading(true);
      setError('');
      
      try {
        const authToken = sessionStorage.getItem('authToken');
        
        // Debug: Check if auth token exists
        if (!authToken) {
          setError('Authentication token not found. Please login again.');
          setLoading(false);
          return;
        }

        console.log('Making API call with token:', authToken ? 'Token exists' : 'No token');
        console.log('Form data:', formData);

        const response = await axios.post(
          'https://tallytobooks-backend-bnezgff5eehsftfj.centralindia-01.azurewebsites.net/api/users/connect-zoho/',
          formData,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Token ${authToken}`
            }
          }
        );

        console.log('Success:', response.data);
        setCompletedSteps([...completedSteps, currentStep]);
        setCurrentStep(currentStep + 1);
        
      } catch (err) {
  console.error('Full error object:', err);

  let errorMessage = 'An unexpected error occurred. Please try again.';

  if (err.response) {
    console.error('Error response:', err.response.data);
    console.error('Error status:', err.response.status);

    const status = err.response.status;
    const data = err.response.data;

    // 1️⃣ Convert string response to lowercase if it's a string:
    if (typeof data === 'string') {
      const responseText = data.trim().toLowerCase();

      // 2️⃣ If the response looks like HTML, show a generic message:
      if (responseText.startsWith('<!doctype') || responseText.startsWith('<html')) {
        errorMessage = `Server Error (${status}): Unexpected server response. Please contact support.`;
      } else {
        // Otherwise, show the plain text response directly:
        errorMessage = data;
      }
    }
    // 3️⃣ If the response is JSON:
    else if (data) {
      if (status === 400 || status === 401 || status === 403) {
        errorMessage = 'Invalid Zoho API credentials. Please check your Client ID, Secret, Tokens, and Organization ID.';
      } else if (status === 404) {
        errorMessage = 'Zoho API endpoint not found. Please verify your API URL and Organization ID.';
      } else if (status >= 500) {
        errorMessage = 'Zoho Books server encountered an internal error. Please try again later or contact support.';
      } else {
        // Fallback: try to extract any error-related fields:
        errorMessage = data.error || data.details?.message || data.message || `Unexpected error. Status: ${status}`;
      }
    } else {
      errorMessage = `Server Error (${status}): ${err.response.statusText || 'Unknown error'}`;
    }

  } else if (err.request) {
    console.error('No response received:', err.request);
    errorMessage = 'No response from server. Please check your internet connection and try again.';
  } else {
    console.error('Request setup error:', err.message);
    errorMessage = `Request Error: ${err.message}`;
  }


        
     showSnackbarAlert(errorMessage);
        
        // Show detailed error in snackbar-style alert for debugging
        showSnackbarAlert(`Error Details:\nStatus: ${err.response?.status || 'No status'}\nMessage: ${errorMessage}\n\nFull Error: ${JSON.stringify(err.response?.data || err.message)}`);
        
      } finally {
        setLoading(false);
      }
    } else if (currentStep === 1) {
      // Move to success page
      setCompletedSteps([...completedSteps, currentStep]);
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      // Remove the current step from completed steps when going back
      setCompletedSteps(completedSteps.filter(step => step !== currentStep));
      setCurrentStep(currentStep - 1);
    }
  };
   const navigate = useNavigate();
  const handleLoginToDashboard = () => {
 
    
    console.log('Redirecting to dashboard...');
    navigate('/dashboard');
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
                      {currentStep === 0 && (
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
              {/* Step 0: Zoho Books Form */}
              {currentStep === 0 && (
                <div className="form-container">
                  <h3 className="form-title">Enter Zoho Books API Credentials :</h3>
                  
                  {currentStepData.formFields.map((field, index) => (
                    <div key={index} className="form-field">
                      <label className="field-label">{field.label}:</label>
                      <input
                        type="text"
                        className="field-input"
                        placeholder={field.placeholder}
                        value={formData[field.name] || ''}
                        onChange={(e) => handleFieldChange(field.name, e.target.value)}
                      />
                    </div>
                  ))}
                  
                  <div className="form-actions">
                    <button onClick={handleNext} className="connect-button" disabled={loading}>
                      {loading ? 'Connecting...' : 'Connect & Proceed'}
                    </button>
                  </div>
                </div>
              )}
              
              {/* Step 1: Tally Integration */}
              {currentStep === 1 && (
                <div className="completion-section ">
                  <div className="completion-content">
                    <h3 className="completion-title">Step 3: Port Data to Zoho</h3>
                    <p className="completion-text">Make sure to install and access the connector from the Zoho Books dashboard.</p>
                    <p className="completion-text">Port</p>
                    <p className="completion-text">Note: Ensure port is valid and accessible.</p>
                    <button onClick={handleNext} className="download-button">
                         <a
      href="/python_agent.exe"   // points to the file in public/
      download="python_agent.exe" // forces download with this name
      className="download-button-a"
    >
      Download Agent.Exe
    </a>
                
                    </button>
                  </div>
                </div>
              )}

              {/* Step 2: Success Message */}
              {currentStep === 2 && (
                <div className="completion-section">
                  <div className="completion-content">
                    <div className="success-icon">
                      <div className="checkmark">✓</div>
                    </div>
                    <h3 className="completion-title">Congratulations!</h3>
                    <p className="completion-text">
                      Your Zoho Books and Tally integration has been successfully configured.
                    </p>
                    <p className="completion-text">
                      You can now access your SyncSonic dashboard to monitor and manage your data synchronization.
                    </p>
                    <button onClick={handleLoginToDashboard} className="complete-setup-button">
                      Login to Dashboard
                    </button>
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
              disabled={currentStep === steps.length - 1 || loading}
              className={`nav-button continue-button ${currentStep === steps.length - 1 ? 'complete' : ''}`}
            >
              {currentStep === 0 ? (loading ? 'Connecting...' : 'Connect & Continue') : 
               currentStep === steps.length - 1 ? 'Complete' : 'Continue'}
            </button>
          </div>
        </div>
      </div>
   {snackbarAlert.show && (
  <div className={`snackbar-alert ${snackbarAlert.type}`}>
    <div className="snackbar-content">
      <div className="snackbar-icon">
        {snackbarAlert.type === 'error' ? '' : 
         snackbarAlert.type === 'success' ? '✅' : 
         snackbarAlert.type === 'warning' ? '⚠️' : 'ℹ️'}
      </div>
      <div className="snackbar-message">
        {snackbarAlert.message.split('\n').map((line, index) => (
          <div key={index} className="snackbar-line">{line}</div>
        ))}
      </div>
      <button className="snackbar-close" onClick={hideSnackbarAlert}>×</button>
    </div>
  </div>
)}
      
   
      {loading && <div className="loading-message">Connecting to Zoho...</div>}
      
     
    </div>
  );
};

export default SyncDataFlow;