import React from 'react';
import './Navigation.css';
import { useNavigate } from 'react-router-dom';

const Navbar = () => {
  // Move the hook inside the component
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/Signin');
  };

  return (
    <nav className="navbar">
      <div className="nav-left">
        <div className="logo">Sync Sonic</div>
      </div>
      <ul className="nav-center">
        <li><a className="active" href="#hero">Home</a></li>
        <li><a href="#services">Services</a></li>
        <li><a href="#whatwedo">What We Do</a></li>
        <li><a href="#MigrationProcess">Migration Process</a></li>
        <li><a href="#support">Support</a></li>
      </ul>
      <div className="nav-right">
        <button className="get-started" onClick={handleGetStarted}>
          Get Started
        </button>
      </div>
    </nav>
  );
};

export default Navbar;