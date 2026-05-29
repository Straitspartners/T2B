import React, { useState } from "react";
import {
  Bell,
  User,
  HelpCircle,
  X,
  RefreshCw,
  Map,
  AlertTriangle,
  CheckCircle,
  UserCheck
} from "lucide-react";
import "./Dashboard.css";
import "./Popup.css";
import Sidebar from "../../../components/Sidebar";

const helpContent = {
  "Getting Started": {
    icon: <User className="popup-title-icon" />,
    content: {
      "Quick Start Guide": [
        "Download and install the migration tool from our official website",
        "Create your account and verify your email address",
        "Complete the initial setup wizard to configure your preferences",
        "Watch our introductory video tutorial for a complete overview",
        "Access the welcome dashboard to begin your migration journey"
      ],
      "System Requirements": [
        "Operating System: Windows 10/11, macOS 10.14+, or Linux Ubuntu 18.04+",
        "RAM: Minimum 4GB, Recommended 8GB or higher",
        "Storage: At least 2GB free disk space for installation",
        "Internet Connection: Stable broadband connection required",
        "Browser: Chrome 90+, Firefox 88+, Safari 14+, or Edge 90+"
      ],
      "Installation Process": [
        "Download the installer package from the official download page",
        "Run the installer with administrator privileges",
        "Follow the installation wizard and accept the license agreement",
        "Choose your installation directory (default recommended)",
        "Wait for the installation to complete and restart if prompted",
        "Launch the application and proceed with initial configuration"
      ],
      "Initial Setup": [
        "Launch the application and create your workspace",
        "Configure your database connection settings",
        "Set up your data source and destination parameters",
        "Test the connection to ensure everything is working properly",
        "Configure security settings and user permissions",
        "Review and save your initial configuration settings"
      ]
    }
  },
  "Migration Process": {
    icon: <RefreshCw className="popup-title-icon" />,
    content: {
      "Data Backup": [
        "Create a complete backup of your source database before starting migration",
        "Verify the backup integrity by performing a test restore",
        "Store backup files in a secure, accessible location",
        "Document the backup process and timestamp for future reference",
        "Consider creating multiple backup copies for redundancy",
        "Test backup restoration process to ensure data recovery capability"
      ],
      "Migration Steps": [
        "Step 1: Analyze source data structure and identify migration requirements",
        "Step 2: Configure mapping rules between source and destination systems",
        "Step 3: Run data validation checks to identify potential issues",
        "Step 4: Execute a test migration with a small data subset",
        "Step 5: Review test results and refine migration parameters",
        "Step 6: Perform the full migration during low-traffic hours",
        "Step 7: Validate migrated data and perform quality assurance checks"
      ],
      "Validation Process": [
        "Compare record counts between source and destination systems",
        "Verify data integrity by spot-checking critical records",
        "Run automated validation scripts to identify discrepancies",
        "Test application functionality with migrated data",
        "Validate relationships and foreign key constraints",
        "Perform user acceptance testing with key stakeholders"
      ],
      "Post-Migration Checklist": [
        "Verify all data has been successfully migrated",
        "Test all system functionalities with the new data",
        "Update system configurations and connection strings",
        "Inform users about the migration completion and any changes",
        "Monitor system performance and address any issues",
        "Archive old system data according to retention policies",
        "Document lessons learned and update migration procedures"
      ]
    }
  },
  "Data Mapping": {
    icon: <Map className="popup-title-icon" />,
    content: {
      "Chart of Accounts": [
        "Map account codes between source and destination systems",
        "Ensure account hierarchies are properly maintained",
        "Validate account types and categories alignment",
        "Handle deprecated accounts and create new mappings as needed",
        "Test account balance calculations after mapping",
        "Document any manual adjustments made during mapping process"
      ],
      "Customer Data": [
        "Map customer IDs and ensure uniqueness in destination system",
        "Transfer contact information including addresses and phone numbers",
        "Migrate customer preferences and communication settings",
        "Preserve customer history and transaction records",
        "Handle duplicate customer records through deduplication process",
        "Validate customer credit limits and payment terms"
      ],
      "Vendor Data": [
        "Map vendor codes and maintain supplier relationships",
        "Transfer vendor contact details and payment information",
        "Migrate purchase history and contract details",
        "Preserve vendor performance metrics and ratings",
        "Handle vendor categorization and classification",
        "Validate payment terms and delivery preferences"
      ],
      "Transaction History": [
        "Preserve chronological order of all transactions",
        "Maintain transaction references and audit trails",
        "Map transaction types and categories correctly",
        "Ensure monetary amounts and currency conversions are accurate",
        "Preserve transaction status and approval workflows",
        "Validate opening balances and carry-forward amounts"
      ]
    }
  },
  "Troubleshooting": {
    icon: <AlertTriangle className="popup-title-icon" />,
    content: {
      "Common Issues": [
        "Connection timeouts: Check network connectivity and firewall settings",
        "Permission errors: Verify user has adequate database privileges",
        "Memory issues: Increase system RAM or adjust batch processing size",
        "Data type mismatches: Review field mappings and data conversions",
        "Performance slowdowns: Optimize queries and consider indexing",
        "Incomplete migrations: Check for interrupted processes and resume options"
      ],
      "Error Messages": [
        "Database connection failed: Verify connection string and credentials",
        "Table not found: Ensure source tables exist and are accessible",
        "Data truncation error: Check field lengths and data formatting",
        "Foreign key constraint violations: Review relationship mappings",
        "Timeout errors: Increase timeout values or reduce batch sizes",
        "Access denied: Check user permissions and security settings"
      ],
      "Data Validation Errors": [
        "Missing required fields: Identify and populate mandatory data",
        "Invalid data formats: Convert data to match destination requirements",
        "Duplicate key violations: Implement deduplication strategies",
        "Referential integrity issues: Resolve broken relationships",
        "Date format inconsistencies: Standardize date formats across systems",
        "Null value handling: Define strategies for missing data"
      ],
      "Connection Issues": [
        "Network connectivity problems: Test network paths and DNS resolution",
        "Firewall blocking connections: Configure firewall rules for migration ports",
        "SSL/TLS certificate issues: Verify and update security certificates",
        "Database server unavailable: Check server status and restart if needed",
        "Authentication failures: Verify credentials and authentication methods",
        "Connection pool exhaustion: Optimize connection usage and limits"
      ]
    }
  },
  "Best Practices": {
    icon: <CheckCircle className="popup-title-icon" />,
    content: {
      "Data Preparation": [
        "Clean and standardize data before migration begins",
        "Remove obsolete records and archive historical data",
        "Validate data integrity and fix inconsistencies",
        "Normalize data formats and naming conventions",
        "Create data dictionaries and mapping documentation",
        "Establish data quality metrics and acceptance criteria"
      ],
      "Migration Planning": [
        "Develop detailed migration timeline with milestones",
        "Identify critical business periods to avoid during migration",
        "Plan for rollback procedures in case of migration failure",
        "Coordinate with stakeholders and communicate schedule",
        "Prepare contingency plans for common migration issues",
        "Allocate sufficient resources and expertise for the project"
      ],
      "Testing Process": [
        "Perform thorough testing in a non-production environment",
        "Test with representative data samples of varying sizes",
        "Validate business logic and workflow processes",
        "Conduct performance testing under expected load conditions",
        "Test disaster recovery and backup restoration procedures",
        "Document test results and obtain stakeholder approval"
      ],
      "Post Migration Tips": [
        "Monitor system performance closely for the first few weeks",
        "Provide user training on any new features or changes",
        "Establish support procedures for migration-related issues",
        "Regular data quality audits and validation checks",
        "Maintain migration documentation for future reference",
        "Gather feedback from users and implement improvements"
      ]
    }
  },
  "User Account": {
    icon: <UserCheck className="popup-title-icon" />,
    content: {
      "General Questions": [
        "How do I reset my password if I forget it?",
        "Can I change my username after account creation?",
        "How do I update my profile information and contact details?",
        "What are the different user roles and their permissions?",
        "How do I enable two-factor authentication for security?",
        "Can I have multiple users access the same migration project?"
      ],
      "Technical Questions": [
        "What are the supported database types and versions?",
        "How do I configure SSL connections for secure data transfer?",
        "What APIs are available for custom integrations?",
        "How do I set up automated migration schedules?",
        "What logging and monitoring capabilities are available?",
        "How do I optimize performance for large data migrations?"
      ],
      "Pricing Questions": [
        "What are the different pricing tiers and their features?",
        "Is there a free trial available for evaluation?",
        "How is pricing calculated for large volume migrations?",
        "Are there discounts available for annual subscriptions?",
        "What payment methods are accepted?",
        "Can I upgrade or downgrade my plan at any time?"
      ],
      "Support Questions": [
        "What support channels are available (email, phone, chat)?",
        "What are the support hours and response time expectations?",
        "Is 24/7 support available for critical migration issues?",
        "How do I escalate urgent technical problems?",
        "Are professional services available for complex migrations?",
        "What training resources and documentation are provided?"
      ]
    }
  }
};

function Help() {
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState(null);

  const handleCardClick = (cardTitle) => {
    setSelectedCard(cardTitle);
    setIsPopupOpen(true);
  };

  const closePopup = () => {
    setIsPopupOpen(false);
    setSelectedCard(null);
  };

  const getCardIcon = (title) => {
    const iconMap = {
      "Getting Started": <User className="card-icon" />,
      "Migration Process": <RefreshCw className="card-icon" />,
      "Data Mapping": <Map className="card-icon" />,
      "Troubleshooting": <AlertTriangle className="card-icon" />,
      "Best Practices": <CheckCircle className="card-icon" />,
      "User Account": <UserCheck className="card-icon" />
    };
    return iconMap[title] || <HelpCircle className="card-icon" />;
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <Sidebar />

        <div className="main-content">
          <div className="header">
            <div className="header-left">
              <h1>Help Center</h1>
              <p>
                Welcome to Our Help Center: Your Resource for Support and
                Guidance
              </p>
            </div>
            <div className="header-right">
              <Bell className="notification-icon" />
              <div className="user-profile">
                <User className="user-icon" />
                <span>John Andrew</span>
              </div>
            </div>
          </div>

          <div className="stats-grid">
            {Object.keys(helpContent).map((cardTitle, index) => (
              <div 
                key={index}
                className="stat-card yellow1 clickable-card" 
                onClick={() => handleCardClick(cardTitle)}
              >
                <div className="stat-content">
                  <h3 style={{ fontWeight: "bold", fontSize: "18px", display: "flex", alignItems: "center", gap: "8px" }}>
                    {getCardIcon(cardTitle)}
                    {cardTitle}
                  </h3>
                  <p className="help-description">
                    {Object.keys(helpContent[cardTitle].content).map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </p>
                </div>
                <div className="sync-button-container"></div>
              </div>
            ))}
          </div>

          <div
            className="content-grid-dashboard"
            style={{ display: "grid", gridTemplateColumns: "1fr" }}
          >
            <h3 className="help-contact-title">Need More Help?</h3>
            <div className="help-options-grid">
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
                    <button type="button" className="chat-link">
                      Start Chat
                    </button>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Popup Modal */}
      {isPopupOpen && selectedCard && (
        <div className="popup-overlay" onClick={closePopup}>
          <div className="popup-container" onClick={(e) => e.stopPropagation()}>
            <div className="popup-header">
              <div className="popup-title">
                {helpContent[selectedCard].icon}
                <h2>{selectedCard}</h2>
              </div>
              <button className="popup-close" onClick={closePopup}>
                <X size={24} />
              </button>
            </div>
            <div className="popup-content">
              {Object.entries(helpContent[selectedCard].content).map(([section, items], index) => (
                <div key={index} className="popup-section">
                  <h3 className="popup-section-title">{section}</h3>
                  <ul className="popup-section-list">
                    {items.map((item, idx) => (
                      <li key={idx} className="popup-section-item">{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Help;
