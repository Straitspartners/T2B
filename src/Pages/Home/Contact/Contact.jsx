import React, { useState } from "react";
import "./Contact.css";
import Support from "D:/tally-to-books/src/assets/support.png"
const ContactForm = () => {
  const [formData, setFormData] = useState({
    fullName: "",
    companyName: "",
    email: "",
    phone: "",
    message: "",
    consent: false,
  });

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("Form submitted:", formData);
  };

  return (
    <div id="support">
      <h4 className="features-title">Ready to Migrate?</h4>
      <p>
        {" "}
<div style={{ textAlign: "center" }}>
  <span className="highlight">Contact us</span>
</div>

      </p>

      <div className="contact-wrapper">
        <div className="contact-left">
          <section id="contact" className="form-section">
            <div className="contact-form" onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="fullName">Full Name:</label>
                  <input
                    type="text"
                    id="fullName"
                    name="fullName"
                    placeholder="Enter your name"
                    value={formData.fullName}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="companyName">Company Name:</label>
                  <input
                    type="text"
                    id="companyName"
                    name="companyName"
                    placeholder="Enter your company name"
                    value={formData.companyName}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="email">Email Address:</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    placeholder="Enter your email address"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="phone">Phone Number:</label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    placeholder="Enter your phone number"
                    value={formData.phone}
                    onChange={handleInputChange}
                    required
                  />
                </div>
              </div>

              <div className="form-group full-width">
                <label htmlFor="message">Message:</label>
                <textarea
                  id="message"
                  name="message"
                  placeholder="Tell us about your migration needs..........."
                  rows="6"
                  value={formData.message}
                  onChange={handleInputChange}
                ></textarea>
              </div>

              <div className="consent-group">
                <input
                  type="checkbox"
                  id="consent"
                  name="consent"
                  checked={formData.consent}
                  onChange={handleInputChange}
                />
                <label htmlFor="consent" className="consent-label">
                  I consent to receiving communications about my inquiry
                </label>
              </div>

              <button
                type="submit"
                className="learn-more-btn blue"
                onClick={handleSubmit}
              >
                Submit Inquiry
              </button>
            </div>
          </section>
        </div>
<div className="step" >

          <div className="step-overlay" style={{ backgroundColor: "transparent" }}>
        <div className="contact-right" >
          <h3 className="contact-title ">Others ways to reach Us</h3>
          <section id="contact-options" className="options-section">
            <div className="options-grid">
              <div className="option-card">
                <div className="icon-wrapper email-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M4 4H20C21.1 4 22 4.9 22 6V18C22 19.1 21.1 20 20 20H4C2.9 20 2 19.1 2 18V6C2 4.9 2.9 4 4 4Z"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <polyline
                      points="22,6 12,13 2,6"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <div className="content">
                  <h4>Email Us</h4>
                  <p className="description">For general inquiries:</p>
                  <p className="contact-info">Demo@gmail.com</p>
                </div>
              </div>

              <div className="option-card">
                <div className="icon-wrapper call-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M22 16.92V19.92C22.0011 20.1985 21.9441 20.4742 21.8325 20.7293C21.7209 20.9845 21.5573 21.2136 21.3521 21.4019C21.1468 21.5901 20.9046 21.7335 20.6407 21.8227C20.3769 21.9119 20.0974 21.9451 19.82 21.92C16.7428 21.5856 13.787 20.5341 11.19 18.85C8.77382 17.3147 6.72533 15.2662 5.19 12.85C3.49998 10.2412 2.44824 7.27099 2.12 4.18C2.09501 3.90347 2.12788 3.62476 2.21649 3.36162C2.3051 3.09849 2.44748 2.85669 2.63519 2.65162C2.82290 2.44655 3.05056 2.28271 3.30391 2.17052C3.55725 2.05833 3.83063 2.00026 4.11 2H7.11C7.59531 1.99522 8.06711 2.16708 8.43849 2.48353C8.80988 2.79999 9.05434 3.23945 9.13 3.72C9.27099 4.68007 9.52566 5.62273 9.89 6.53C10.0213 6.88792 10.0618 7.27691 10.0083 7.65088C9.95478 8.02485 9.80967 8.38103 9.59 8.68L8.26 10.01C9.69097 12.4135 11.5865 14.309 14 15.74L15.32 14.41C15.6191 14.1903 15.9752 14.0452 16.3492 13.9917C16.7231 13.9382 17.1121 13.9787 17.47 14.11C18.3773 14.4743 19.3199 14.729 20.28 14.87C20.7658 14.9466 21.2094 15.1965 21.5265 15.5739C21.8437 15.9513 22.0122 16.4296 22 16.92Z"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <div className="content">
                  <h4>Call Us</h4>
                  <p className="description">Monday to Friday, 9am to 6pm:</p>
                  <p className="contact-info">+91 9999999999</p>
                </div>
              </div>

              <div className="option-card">
                <div className="icon-wrapper chat-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <div className="content">
                  <h4>Live Chat</h4>
                  <p className="description">Chat with our support team:</p>
                  <p className="contact-info">
                    <a href="#" className="chat-link">
                      Start Chat
                    </a>
                  </p>
                </div>
        
              </div>
                      <img src={Support}  alt="Chat Icon" className="chat-icon-image" />
            </div>
          </section>
        </div>
        </div>
        </div>
      </div>
    </div>
  );
};

export default ContactForm;
