import React, { useState } from 'react';
import './Footer.css';

const Footer = () => {
  const [email, setEmail] = useState('');

  const handleSubscribe = () => {
    console.log('Subscribing:', email);
    // Handle subscription logic here
    setEmail('');
  };

  return (
    <footer className="footer">
      <div className="footer-container">
        {/* Company Info Section */}
        <div className="footer-section company-info">
          <h2 className="company-name">Sync Sonic</h2>
          <div className="contact-info">
            <div className="contact-item">
              <svg className="icon location-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              <span>123 Example Road New York, NY 12345</span>
            </div>
            <div className="contact-item">
              <svg className="icon email-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              <span>email@example.com</span>
            </div>
            <div className="contact-item">
              <svg className="icon phone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
              </svg>
              <span>(555) 555-5555</span>
            </div>
          </div>
        </div>

        {/* Useful Links Section */}
        <div className="footer-section useful-links">
          <h3 className="section-title">Useful Link</h3>
          <ul className="links-list">
            <li><a href="#what-we-do">What We Do</a></li>
            <li><a href="#services">Services</a></li>
            <li><a href="#testimonials">Testimonials</a></li>
            <li><a href="#support">Support</a></li>
          </ul>
        </div>

        {/* Follow Us Section */}
        <div className="footer-section follow-us">
          <h3 className="section-title">Follow Us</h3>
          <div className="social-links">
            <a href="#linkedin" className="social-link">LinkedIn</a>
          </div>
        </div>

        {/* Newsletter Section */}
        <div className="footer-section newsletter">
          <h3 className="section-title">Subscribe our newsletter</h3>
                <div className="hero-input">
        <input type="email" placeholder="Your email address" />
        <button>Subscribe</button>
      </div>
        </div>
      </div>

      {/* Copyright */}
      <div className="footer-bottom">
        <p className="copyright">Copyright © 2025</p>
      </div>
    </footer>
  );
};

export default Footer;