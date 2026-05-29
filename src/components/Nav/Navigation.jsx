import React from 'react';
import './Navigation.css';
import { useNavigate } from 'react-router-dom';

const Navbar = () => {
  // Move the hook inside the component
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/signin');
  };

  return (
    <nav className="navbar">
      <div className="nav-left">
        <div className="logo">Tally2Books</div>
      </div>
      <ul className="nav-center">
        <li><a className="active" href="#hero">Home</a></li>
        <li><a href="#services">Services</a></li>
        <li><a href="#whatwedo">What We Do</a></li>
        <li><a href="#migration-process">Migration Process</a></li>
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
