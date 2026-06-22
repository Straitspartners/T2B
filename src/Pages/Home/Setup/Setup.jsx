import React, { useState, useEffect } from 'react';
import './Setup.css';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const ZOHO_AUTH_URL = 'https://accounts.zoho.in/oauth/v2/auth';
const REDIRECT_URI  = 'http://localhost:3000/setup';
const DJANGO_BASE   = 'http://127.0.0.1:8000';

const SyncDataFlow = () => {
  const [currentStep, setCurrentStep]       = useState(0);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [loading, setLoading]               = useState(false);
  const [tokenLoading, setTokenLoading]     = useState(false);
  const [snackbarAlert, setSnackbarAlert]   = useState({ show: false, message: '', type: 'error' });

  const [formData, setFormData] = useState({
    client_id:       '',
    client_secret:   '',
    access_token:    '',
    refresh_token:   '',
    organization_id: '',
  });

  // ─── On mount: check if Zoho redirected back with ?code= ───────────────────
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code   = params.get('code');
    if (!code) return;

    // Clean the code out of the URL immediately so a refresh doesn't re-trigger
    window.history.replaceState({}, document.title, '/setup');

    // Retrieve the credentials we saved before redirecting to Zoho
    const savedClientId     = sessionStorage.getItem('zoho_client_id');
    const savedClientSecret = sessionStorage.getItem('zoho_client_secret');
    const savedOrgId        = sessionStorage.getItem('zoho_org_id');

    if (!savedClientId || !savedClientSecret) {
      showSnackbarAlert('Session expired. Please enter your Client ID & Secret again and retry.', 'error');
      return;
    }

    // Restore form fields so the user can see what's there
    setFormData(prev => ({
      ...prev,
      client_id:       savedClientId,
      client_secret:   savedClientSecret,
      organization_id: savedOrgId || prev.organization_id,
    }));

    exchangeCodeForTokens(code, savedClientId, savedClientSecret, savedOrgId);
  }, []);

  // ─── Exchange auth code → tokens via Django ────────────────────────────────
  const exchangeCodeForTokens = async (code, clientId, clientSecret, orgId) => {
    setTokenLoading(true);
    try {
      const response = await axios.post(
        `${DJANGO_BASE}/api/zoho/exchange-code/`,
        {
          client_id:     clientId,
          client_secret: clientSecret,
          code,
          redirect_uri:  REDIRECT_URI,
        }
      );

      const { access_token, refresh_token } = response.data;

      setFormData(prev => ({
        ...prev,
        client_id:       clientId,
        client_secret:   clientSecret,
        organization_id: orgId || prev.organization_id,
        access_token,
        refresh_token,
      }));

      // Clean up sessionStorage
      sessionStorage.removeItem('zoho_client_id');
      sessionStorage.removeItem('zoho_client_secret');
      sessionStorage.removeItem('zoho_org_id');

      showSnackbarAlert('Tokens generated successfully! Review and click "Connect & Proceed".', 'success');
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to generate tokens. Please try again.';
      showSnackbarAlert(msg, 'error');
    } finally {
      setTokenLoading(false);
    }
  };

  // ─── "Generate Tokens" button handler ─────────────────────────────────────
  const handleGenerateTokens = () => {
    const { client_id, client_secret } = formData;

    if (!client_id.trim()) {
      showSnackbarAlert('Please enter your Client ID first.', 'error');
      return;
    }
    if (!client_secret.trim()) {
      showSnackbarAlert('Please enter your Client Secret first.', 'error');
      return;
    }

    // Save credentials to sessionStorage so we can retrieve them after redirect
    sessionStorage.setItem('zoho_client_id',     client_id.trim());
    sessionStorage.setItem('zoho_client_secret', client_secret.trim());
    sessionStorage.setItem('zoho_org_id',        formData.organization_id.trim());

    // Build Zoho OAuth URL and redirect the browser
    const authParams = new URLSearchParams({
      response_type: 'code',
      client_id:     client_id.trim(),
      scope:         'ZohoBooks.fullaccess.all',
      redirect_uri:  REDIRECT_URI,
      access_type:   'offline',
      prompt:        'consent',
    });

    window.location.href = `${ZOHO_AUTH_URL}?${authParams.toString()}`;
  };

  // ─── Steps definition ──────────────────────────────────────────────────────
  const steps = [
    {
      title: 'Connect Zoho Books Account',
      subtitle: 'Securely connect your Zoho Books account to begin the migration process from Tally. Your credentials are encrypted and never stored.',
      sections: [
        {
          title: 'How to get Zoho Books API Credentials',
          subsections: [
            {
              title: '1. Client ID & Client Secret',
              steps: [
                'Go to Zoho API Console (api-console.zoho.in).',
                'Create a new client — choose "Server-based" client.',
                'Set the redirect URI to: http://localhost:3000/setup',
                'Copy the Client ID and Client Secret and paste them below.',
              ],
            },
            {
              title: '2. Generate Tokens (Automated)',
              steps: [
                'Enter Client ID, Client Secret, and Organisation ID below.',
                'Click "Generate Tokens" — your browser will open Zoho login.',
                'Log in and approve access.',
                'You\'ll be redirected back here with tokens auto-filled.',
              ],
            },
            {
              title: '3. Organization ID',
              steps: [
                'Login to Zoho Books.',
                'Go to Settings → Organization Profile.',
                "You'll find the Organization ID in the URL or API response.",
              ],
            },
          ],
        },
      ],
      formFields: [], // rendered manually below
    },
    {
      title: 'Connect Tally Account',
      subtitle: 'Ready to Migrate? Connect to continue the migration process from Tally to Zoho Books.',
      sections: [
        {
          title: 'How to Connect Tally with Zoho Books',
          subsections: [
            {
              title: 'Step 1: Port Data to Zoho',
              steps: ['Make sure to install and access the connector from the Zoho Books dashboard.'],
            },
            {
              title: 'Step 2: Run the Sync Agent',
              steps: [
                'Download and install the Sync Agent on the system where TallyPrime is running.',
                'Configure the Sync Agent with your Zoho Books credentials.',
                'Start the Sync Agent.',
              ],
            },
            {
              title: 'Step 3: Configure Tally',
              steps: [
                'Open TallyPrime.',
                'Configure TallyPrime to communicate with the Sync Agent.',
                'Verify the connection.',
              ],
            },
          ],
        },
      ],
      formFields: [],
    },
    {
      title: 'Setup Complete!',
      subtitle: 'Your Zoho Books and Tally integration has been successfully configured.',
      sections: [
        {
          title: "What's Next?",
          subsections: [
            {
              title: 'Access Your Dashboard',
              steps: [
                'Your integration is now ready to use.',
                'You can now access all features from your SyncSonic dashboard.',
                'Monitor your data synchronization in real-time.',
              ],
            },
          ],
        },
      ],
      formFields: [],
    },
  ];

  const stepTitles = ['Zoho Books Integration', 'Tally Integration', 'SyncSonic Dashboard'];

  // ─── Snackbar helpers ──────────────────────────────────────────────────────
  const showSnackbarAlert = (message, type = 'error') => {
    setSnackbarAlert({ show: true, message, type });
    setTimeout(() => setSnackbarAlert({ show: false, message: '', type: 'error' }), 8000);
  };

  const hideSnackbarAlert = () => setSnackbarAlert({ show: false, message: '', type: 'error' });

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
  };

  // ─── Next / Back ───────────────────────────────────────────────────────────
  const handleNext = async () => {
    if (currentStep === 0) {
      const requiredFields = ['client_id', 'client_secret', 'access_token', 'refresh_token', 'organization_id'];
      const emptyFields    = requiredFields.filter(f => !formData[f]?.trim());

      if (emptyFields.length > 0) {
        showSnackbarAlert(`Please fill in all required fields: ${emptyFields.join(', ')}`);
        return;
      }

      setLoading(true);
      try {
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
          setLoading(false);
          showSnackbarAlert('Authentication token not found. Please login again.');
          return;
        }

        await axios.post(
          `${DJANGO_BASE}/api/connect-zoho/`,
          formData,
          { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` } }
        );

        setCompletedSteps([...completedSteps, currentStep]);
        setCurrentStep(currentStep + 1);
      } catch (err) {
        let errorMessage = 'An unexpected error occurred. Please try again.';
        if (err.response) {
          const { status, data } = err.response;
          if (typeof data === 'string') {
            const lower = data.trim().toLowerCase();
            errorMessage = lower.startsWith('<!doctype') || lower.startsWith('<html')
              ? `Server Error (${status}): Unexpected server response.`
              : data;
          } else if (data) {
            if (status === 400 || status === 401 || status === 403)
              errorMessage = 'Invalid Zoho API credentials. Please check your details.';
            else if (status === 404)
              errorMessage = 'Zoho API endpoint not found. Verify your Organisation ID.';
            else if (status >= 500)
              errorMessage = 'Zoho Books server error. Please try again later.';
            else
              errorMessage = data.error || data.message || `Unexpected error. Status: ${status}`;
          }
        } else if (err.request) {
          errorMessage = 'No response from server. Check your connection.';
        } else {
          errorMessage = `Request Error: ${err.message}`;
        }
        showSnackbarAlert(errorMessage);
      } finally {
        setLoading(false);
      }
    } else if (currentStep === 1) {
      setCompletedSteps([...completedSteps, currentStep]);
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCompletedSteps(completedSteps.filter(s => s !== currentStep));
      setCurrentStep(currentStep - 1);
    }
  };

  const navigate = useNavigate();
  const handleLoginToDashboard = () => navigate('/quick-migration');

  // ─── Step indicator component ──────────────────────────────────────────────
  const StepIndicator = ({ stepIndex, isActive, isCompleted }) => (
    <div className="step-indicator">
      <div className={`step-circle ${isCompleted ? 'completed' : isActive ? 'active' : 'inactive'}`}>
        {stepIndex + 1}
      </div>
      <div className="step-label">{stepTitles[stepIndex]}</div>
      {stepIndex < steps.length - 1 && (
        <div className={`step-line ${completedSteps.includes(stepIndex) ? 'completed' : 'inactive'}`} />
      )}
    </div>
  );

  const currentStepData = steps[currentStep];

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="sync-data-container">
      <div className="sync-data-wrapper">

        {/* Header */}
        <div className="header">
          <h1 className="logo">Tally2books</h1>
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
            {/* Instructions */}
            <div className="instructions-section">
              {currentStepData.sections.map((section, sIdx) => (
                <div key={sIdx} className="section">
                  <h3 className="section-title">{section.title}</h3>
                  {section.subsections && (
                    <div className="subsections">
                      {section.subsections.map((sub, subIdx) => (
                        <div key={subIdx} className="subsection">
                          <h4 className="subsection-title">{sub.title}</h4>
                          {sub.steps && (
                            <ul className="subsection-steps">
                              {sub.steps.map((s, sI) => (
                                <li key={sI} className="subsection-step">{s}</li>
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

            {/* Form */}
            <div className="form-section">

              {/* ── Step 0: Zoho Credentials ── */}
              {currentStep === 0 && (
                <div className="form-container">
                  <h3 className="form-title">Enter Zoho Books API Credentials :</h3>

                  {/* Client ID */}
                  <div className="form-field">
                    <label className="field-label">Client ID:</label>
                    <input
                      type="text"
                      className="field-input"
                      placeholder="Enter your Client ID"
                      value={formData.client_id}
                      onChange={e => handleFieldChange('client_id', e.target.value)}
                    />
                  </div>

                  {/* Client Secret */}
                  <div className="form-field">
                    <label className="field-label">Client Secret:</label>
                    <input
                      type="text"
                      className="field-input"
                      placeholder="Enter your Client Secret"
                      value={formData.client_secret}
                      onChange={e => handleFieldChange('client_secret', e.target.value)}
                    />
                  </div>

                  {/* Organisation ID */}
                  <div className="form-field">
                    <label className="field-label">Organization ID:</label>
                    <input
                      type="text"
                      className="field-input"
                      placeholder="Enter your Organization ID"
                      value={formData.organization_id}
                      onChange={e => handleFieldChange('organization_id', e.target.value)}
                    />
                  </div>

                  {/* ── Token Section ── */}
                  <div className="token-section">
                    <div className="token-section-header">
                      <span className="token-section-title">Access & Refresh Tokens</span>
                      <button
                        className="generate-tokens-button"
                        onClick={handleGenerateTokens}
                        disabled={tokenLoading}
                        title="Opens Zoho login in this tab. You'll be redirected back automatically."
                      >
                        {tokenLoading ? (
                          <>
                            <span className="btn-spinner" /> Generating...
                          </>
                        ) : (
                          <>⚡ Generate Tokens</>
                        )}
                      </button>
                    </div>

                    {/* Show token fields — read-only when auto-filled, editable if user wants to paste manually */}
                    <div className="form-field">
                      <label className="field-label">
                        Access Token:
                        {formData.access_token && (
                          <span className="token-filled-badge">✓ Auto-filled</span>
                        )}
                      </label>
                      <input
                        type="text"
                        className={`field-input ${formData.access_token ? 'token-filled' : ''}`}
                        placeholder="Click 'Generate Tokens' or paste manually"
                        value={formData.access_token}
                        onChange={e => handleFieldChange('access_token', e.target.value)}
                      />
                    </div>

                    <div className="form-field">
                      <label className="field-label">
                        Refresh Token:
                        {formData.refresh_token && (
                          <span className="token-filled-badge">✓ Auto-filled</span>
                        )}
                      </label>
                      <input
                        type="text"
                        className={`field-input ${formData.refresh_token ? 'token-filled' : ''}`}
                        placeholder="Click 'Generate Tokens' or paste manually"
                        value={formData.refresh_token}
                        onChange={e => handleFieldChange('refresh_token', e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="form-actions">
                    <button onClick={handleNext} className="connect-button" disabled={loading}>
                      {loading ? 'Connecting...' : 'Connect & Proceed'}
                    </button>
                  </div>
                </div>
              )}

              {/* ── Step 1: Tally Agent ── */}
              {currentStep === 1 && (
                <div className="completion-section">
                  <div className="completion-content">
                    <h3 className="completion-title">Step 3: Port Data to Zoho</h3>
                    <p className="completion-text">Make sure to install and access the connector from the Zoho Books dashboard.</p>
                    <p className="completion-text">Port</p>
                    <p className="completion-text">Note: Ensure port is valid and accessible.</p>
                    <button onClick={handleNext} className="download-button">
                      <a href="/python_agent.exe" download="python_agent.exe" className="download-button-a">
                        Download Agent.Exe
                      </a>
                    </button>
                  </div>
                </div>
              )}

              {/* ── Step 2: Success ── */}
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
                      You can now access your SyncSonic dashboard to monitor and manage your data synchronisation.
                    </p>
                    <button onClick={handleLoginToDashboard} className="complete-setup-button">
                      Login to Dashboard
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Navigation */}
          <div className="navigation">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className={`nav-button back-button ${currentStep === 0 ? 'disabled' : ''}`}
            >
              Back
            </button>
            <div className="step-counter">Step {currentStep + 1} of {steps.length}</div>
            <button
              onClick={handleNext}
              disabled={currentStep === steps.length - 1 || loading}
              className={`nav-button continue-button ${currentStep === steps.length - 1 ? 'complete' : ''}`}
            >
              {currentStep === 0
                ? loading ? 'Connecting...' : 'Connect & Continue'
                : currentStep === steps.length - 1
                  ? 'Complete'
                  : 'Continue'}
            </button>
          </div>
        </div>
      </div>

      {/* Snackbar */}
      {snackbarAlert.show && (
        <div className={`snackbar-alert ${snackbarAlert.type}`}>
          <div className="snackbar-content">
            <div className="snackbar-icon">
              {snackbarAlert.type === 'error'   ? '❌' :
               snackbarAlert.type === 'success' ? '✅' :
               snackbarAlert.type === 'warning' ? '⚠️' : 'ℹ️'}
            </div>
            <div className="snackbar-message">
              {snackbarAlert.message.split('\n').map((line, i) => (
                <div key={i} className="snackbar-line">{line}</div>
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