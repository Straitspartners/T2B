import React, { useState } from "react";
import './Auth.css'; // Assuming you have a CSS file for styles
const AuthPage = () => {
  const [isSignIn, setIsSignIn] = useState(true);
  const [signInForm, setSignInForm] = useState({ email: '', password: '', remember: false });
  const [signUpForm, setSignUpForm] = useState({ 
    name: '', 
    email: '', 
    password: '', 
    confirmPassword: '' 
  });
  
  const handleSignInChange = e => {
    const { name, value, type, checked } = e.target;
    setSignInForm(f => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
  };
  
  const handleSignUpChange = e => {
    const { name, value } = e.target;
    setSignUpForm(f => ({ ...f, [name]: value }));
  };
  
  const handleSignInSubmit = e => {
    e.preventDefault();
    console.log('Sign In - Email:', signInForm.email, 'Password:', signInForm.password, 'Remember Me:', signInForm.remember);
  };
  
  const handleSignUpSubmit = e => {
    e.preventDefault();
    if (signUpForm.password !== signUpForm.confirmPassword) {
      alert('Passwords do not match!');
      return;
    }
    console.log('Sign Up - Name:', signUpForm.name, 'Email:', signUpForm.email, 'Password:', signUpForm.password);
  };

  return (
    <div className="sync-container">
      <div className="sync-left">
        <div className="sync-content">
          <h1 className="sync-brand">Sync Sonic</h1>
          <h2 className="sync-title">Speed up your data migration faster with Syncsonic</h2>
          
          <div className="sync-logos">
            <div className="logo-item">
              <div className="logo-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
              </div>
              <span className="logo-text">Zoho<br/>Books</span>
            </div>
            
            <div className="logo-item">
              <div className="logo-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3M19,19H5V5H19V19Z"/>
                </svg>
              </div>
              <span className="logo-text">Tally<br/>Prime</span>
            </div>
            
            <div className="logo-item">
              <div className="logo-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
              </div>
              <span className="logo-text">Zoho<br/>Books</span>
            </div>
            
            <div className="logo-item">
              <div className="logo-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3M19,19H5V5H19V19Z"/>
                </svg>
              </div>
              <span className="logo-text">Tally<br/>Prime</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="sync-right">
        <div className="auth-form">
          <div className="header">
            <h1 className="welcome">
              {isSignIn ? 'Welcome Back' : 'Create Account'}
            </h1>
            <div className="auth-links">
              <button 
                className={`auth-tab ${isSignIn ? 'active-link' : ''}`}
                onClick={() => setIsSignIn(true)}
              >
                Sign In
              </button>
              <button 
                className={`auth-tab ${!isSignIn ? 'active-link' : ''}`}
                onClick={() => setIsSignIn(false)}
              >
                Sign Up
              </button>
            </div>
          </div>
          
          {isSignIn ? (
            <div className="form">
              <label>Email id :</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20,8L12,13L4,8V6L12,11L20,6M20,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V6C22,4.89 21.1,4 20,4Z"/>
                </svg>
                <input 
                  type="email" 
                  name="email" 
                  placeholder="Enter your email address" 
                  value={signInForm.email} 
                  onChange={handleSignInChange} 
                  required 
                />
              </div>
              
              <label>Password :</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
                </svg>
                <input 
                  type="password" 
                  name="password" 
                  placeholder="Enter your Password here" 
                  value={signInForm.password} 
                  onChange={handleSignInChange} 
                  required 
                />
              </div>
              
              <div className="options">
                <label className="checkbox-label">
                  <input 
                    type="checkbox" 
                    name="remember" 
                    checked={signInForm.remember} 
                    onChange={handleSignInChange} 
                  /> 
                  Remember Password
                </label>
                <a href="#" className="forgot-link">Forgot Password ?</a>
              </div>
              
              <button type="submit" className="btn-blue" onClick={handleSignInSubmit}>Sign In</button>
              
              <div className="divider">Or Continue With</div>
              
              <button type="button" className="google-btn" aria-label="Sign in with Google">
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google
              </button>
            </div>
          ) : (
            <div className="form">
              <label>Your Account Name :</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/>
                </svg>
                <input 
                  type="text" 
                  name="name" 
                  placeholder="Enter your Name here" 
                  value={signUpForm.name} 
                  onChange={handleSignUpChange} 
                  required 
                />
              </div>
              
              <label>Email id :</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20,8L12,13L4,8V6L12,11L20,6M20,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V6C22,4.89 21.1,4 20,4Z"/>
                </svg>
                <input 
                  type="email" 
                  name="email" 
                  placeholder="Enter your email address" 
                  value={signUpForm.email} 
                  onChange={handleSignUpChange} 
                  required 
                />
              </div>
              
              <label>Password :</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
                </svg>
                <input 
                  type="password" 
                  name="password" 
                  placeholder="Create Password in 8+ characters" 
                  value={signUpForm.password} 
                  onChange={handleSignUpChange} 
                  minLength="8"
                  required 
                />
              </div>
              
              <label>Confirm Password :</label>
              <div className="input-wrapper">
                <svg className="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z"/>
                </svg>
                <input 
                  type="password" 
                  name="confirmPassword" 
                  placeholder="Enter the password again" 
                  value={signUpForm.confirmPassword} 
                  onChange={handleSignUpChange} 
                  required 
                />
              </div>
              
              <button type="submit" className="btn-blue" onClick={handleSignUpSubmit}>Create Account</button>
              
              <div className="divider">Or Create With</div>
              
              <button type="button" className="google-btn" aria-label="Sign up with Google">
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Signup with Google
              </button>
            </div>
          )}
        </div>
      </div>
      
     
    </div>
  );
};

export default AuthPage;