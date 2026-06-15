import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Sidebar.css";

function Sidebar() {
  const { pathname } = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isTransactionsDropdownOpen, setIsTransactionsDropdownOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const checkScreenSize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      if (!mobile) {
        setIsMobileMenuOpen(false);
      }
    };

    checkScreenSize();
    window.addEventListener("resize", checkScreenSize);
    return () => window.removeEventListener("resize", checkScreenSize);
  }, []);

  useEffect(() => {
    if (isMobile) {
      setIsMobileMenuOpen(false);
    }
  }, [pathname, isMobile]);

  // Check if current path is a masters submenu item
  useEffect(() => {
    const mastersSubItems = [
      "/masters/customers",
      "/masters/vendors",
      "/masters/chart-of-accounts",
      "/masters/items",
    ];
    if (mastersSubItems.includes(pathname) || pathname === "/masters") {
      setIsDropdownOpen(true);
    }
  }, [pathname]);

  // Check if current path is a transactions submenu item
  useEffect(() => {
    const transactionsSubItems = [
      "/transactions/invoice",
      "/transactions/payment-received",
      "/transactions/credit-notes",
      "/transactions/bills",
      "/transactions/payment-made",
      "/transactions/vendor-credit",
      "/transactions/expenses",
      "/transactions/manual-journals",
    ];
    if (transactionsSubItems.includes(pathname) || pathname === "/transactions") {
      setIsTransactionsDropdownOpen(true);
    }
  }, [pathname]);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const toggleDropdown = (e) => {
    e.preventDefault();
    setIsDropdownOpen(!isDropdownOpen);
  };

  const toggleTransactionsDropdown = (e) => {
    e.preventDefault();
    setIsTransactionsDropdownOpen(!isTransactionsDropdownOpen);
  };

  const upgrade = () => {
    navigate("/upgrade");
    closeMobileMenu();
  };

  // Check if any masters submenu is active
  const isMastersActive = () => {
    return (
      pathname === "/masters" ||
      pathname.startsWith("/masters/customers") ||
      pathname.startsWith("/masters/vendors") ||
      pathname.startsWith("/masters/chart-of-accounts") ||
      pathname.startsWith("/masters/items")
    );
  };

  // Check if any transactions submenu is active
  const isTransactionsActive = () => {
    return (
      pathname === "/transactions" ||
      pathname.startsWith("/transactions/invoice") ||
      pathname.startsWith("/transactions/payment-received") ||
      pathname.startsWith("/transactions/credit-notes") ||
      pathname.startsWith("/transactions/bills") ||
      pathname.startsWith("/transactions/payment-made") ||
      pathname.startsWith("/transactions/vendor-credit") ||
      pathname.startsWith("/transactions/expenses") ||
      pathname.startsWith("/transactions/manual-journals")
    );
  };

  return (
    <>
      <div className="dashboard-page">
        {/* Mobile Menu Toggle - Only shows on mobile */}
        {isMobile && (
          <button
            className="mobile-menu-toggle"
            onClick={toggleMobileMenu}
            aria-label="Toggle navigation menu"
          >
            <div className={`hamburger ${isMobileMenuOpen ? "active" : ""}`}>
              <span></span>
              <span></span>
              <span></span>
            </div>
          </button>
        )}

        {/* Overlay - Only shows on mobile */}
        {isMobile && (
          <div
            className={`overlay ${isMobileMenuOpen ? "active" : ""}`}
            onClick={closeMobileMenu}
          />
        )}

        {/* Your original sidebar with responsive class */}
        <div className={`sidebar ${isMobileMenuOpen ? "mobile-active" : ""}`}>
          <div className="sidebar-header">
            <h2 className="logo">Tally2Books</h2>
          </div>

          <nav className="sidebar-nav">
            <Link
              to="/dashboard"
              className={`nav-item ${
                pathname === "/dashboard" ? "active" : ""
              }`}
            >
              Dashboard
            </Link>

            <Link
              to="/quick-migration"
              className={`nav-item ${
                pathname === "/quick-migration" ? "active" : ""
              }`}
            >
              Quick Migration
            </Link>

            {/* Masters dropdown */}
            <div className="dropdown-container">
              <div onClick={toggleDropdown}>
                <Link
                  to="/masters"
                  className={`nav-item dropdown-toggle ${
                    isMastersActive() ? "active" : ""
                  }`}
                >
                  <span>Masters</span>
                  <span
                    className={`dropdown-arrow ${isDropdownOpen ? "open" : ""}`}
                  >
                    ▼
                  </span>
                </Link>
              </div>

              {isDropdownOpen && (
                <div className="dropdown-menu">
                  <Link
                    to="/customers"
                    className={`dropdown-item ${
                      pathname === "/customers" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Customers
                  </Link>
                  <Link
                    to="/vendors"
                    className={`dropdown-item ${
                      pathname === "/vendors" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Vendors
                  </Link>
                  <Link
                    to="/chart-of-accounts"
                    className={`dropdown-item ${
                      pathname === "/chart-of-accounts" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Chart of Accounts
                  </Link>
                  <Link
                    to="/items"
                    className={`dropdown-item ${
                      pathname === "/items" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Items
                  </Link>
                </div>
              )}
            </div>

            {/* Transactions dropdown */}
            <div className="dropdown-container">
              <div onClick={toggleTransactionsDropdown}>
                <Link
                  to="/transactions"
                  className={`nav-item dropdown-toggle ${
                    isTransactionsActive() ? "active" : ""
                  }`}
                >
                  <span>Transactions</span>
                  <span
                    className={`dropdown-arrow ${isTransactionsDropdownOpen ? "open" : ""}`}
                  >
                    ▼
                  </span>
                </Link>
              </div>

              {isTransactionsDropdownOpen && (
                <div className="dropdown-menu">
                  <Link
                    to="/invoice"
                    className={`dropdown-item ${
                      pathname === "/invoice" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Invoice
                  </Link>
                  <Link
                    to="/payment-received"
                    className={`dropdown-item ${
                      pathname === "/payment-received" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Payment Received
                  </Link>
                  <Link
                    to="/credit-notes"
                    className={`dropdown-item ${
                      pathname === "/credit-notes" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Credit Notes
                  </Link>
                  <Link
                    to="/bills"
                    className={`dropdown-item ${
                      pathname === "/bills" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Bills
                  </Link>
                  <Link
                    to="/payment-made"
                    className={`dropdown-item ${
                      pathname === "/payment-made" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Payment Made
                  </Link>
                  <Link
                    to="/vendor-credit"
                    className={`dropdown-item ${
                      pathname === "/vendor-credit" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Vendor Credit
                  </Link>
                  <Link
                    to="/expenses"
                    className={`dropdown-item ${
                      pathname === "/expenses" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Expenses
                  </Link>
                  <Link
                    to="/manual-journals"
                    className={`dropdown-item ${
                      pathname === "/manual-journals" ? "active" : ""
                    }`}
                    onClick={closeMobileMenu}
                  >
                    Manual Journals
                  </Link>
                </div>
              )}
            </div>

            <Link
              to="/settings"
              className={`nav-item ${pathname === "/settings" ? "active" : ""}`}
            >
              Settings
            </Link>
          </nav>

          <div className="sidebar-support">
            <h3>Support</h3>
            <Link to="/help" className={`nav-item ${pathname === "/help" ? "active" : ""}`}>
              Help Center
            </Link>
          </div>

          <div className="sidebar-upgrade">
            <div className="upgrade-icon">
              <div className="triangle"></div>
            </div>
            <button className="upgrade-btn" onClick={upgrade}>
              Upgrade Now
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

export default Sidebar;
