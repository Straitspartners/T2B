import './App.css';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Signin from './Auth/Signin';
import Signup from './Auth/Signup';
import Nav from './components/Nav/Navigation';
import Herosection from './Pages/Home/HeroSection/HeroSection';
import Services from './Pages/Home/Services/Services';
import Whatwedo from './Pages/Home/WhatWeDo/WhatWeDo';
import Migration from './Pages/Home/MigrationProcess/MigrationProcess';
import Contact from './Pages/Home/Contact/Contact';
import Faq from './Pages/Home/FAQ/FAQ';
import Footer from './Pages/Home/Footer/Footer';
import Setup from './Pages/Home/Setup/Setup';
import Sidebar from './components/Sidebar';

// Dashboard pages
import Dashboard from './Pages/Home/Dashboard/Dashboard';
import Masters from './Pages/Home/Dashboard/Masters';
import Transactions from './Pages/Home/Dashboard/Transactions';
import Help from './Pages/Home/Dashboard/Help';
import ContactSupport from './Pages/Home/Dashboard/ContactSupport';
import Settings from './Pages/Home/Dashboard/Settings';
import Upgrade from './Pages/Home/Dashboard/Upgrade';
import QuickMigration from './Pages/Home/Dashboard/QuickMigration';

// Masters sub-pages
import Customers from './Pages/Home/Dashboard/Customers';
import Vendors from './Pages/Home/Dashboard/Vendors';
import Chartofaccounts from './Pages/Home/Dashboard/ChartofAC';
import Items from './Pages/Home/Dashboard/Item';

// Transaction sub-pages
import Invoice from './Pages/Home/Dashboard/Invoice';
import PaymentReceived from './Pages/Home/Dashboard/PaymentReceived';
import CreditNotes from './Pages/Home/Dashboard/CreditNotes';
import Bills from './Pages/Home/Dashboard/Bills';
import PaymentMade from './Pages/Home/Dashboard/PaymentMade';
import VendorCredit from './Pages/Home/Dashboard/VendorCredit';
import Expenses from './Pages/Home/Dashboard/Expenses';
import ManualJournals from './Pages/Home/Dashboard/ManualJournals';

function HomePage() {
  return (
    <>
      <Nav />
      <Herosection />
      <Services />
      <Whatwedo />
      <Migration />
      <Contact />
      <Faq />
      <Footer />
    </>
  );
}

function App() {
  return (
    <div className="App">
      <Router>
        <Routes>
          {/* Public */}
          <Route path="/" element={<HomePage />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/signin" element={<Signin />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/setup" element={<Setup />} />

          {/* Dashboard shell */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/sidebar" element={<Sidebar />} />
          <Route path="/quick-migration" element={<QuickMigration />} />

          {/* Masters */}
          <Route path="/masters" element={<Masters />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/vendors" element={<Vendors />} />
          <Route path="/chart-of-accounts" element={<Chartofaccounts />} />
          <Route path="/items" element={<Items />} />

          {/* Transactions */}
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/invoice" element={<Invoice />} />
          <Route path="/payment-received" element={<PaymentReceived />} />
          <Route path="/credit-notes" element={<CreditNotes />} />
          <Route path="/bills" element={<Bills />} />
          <Route path="/payment-made" element={<PaymentMade />} />
          <Route path="/vendor-credit" element={<VendorCredit />} />
          <Route path="/expenses" element={<Expenses />} />
          <Route path="/manual-journals" element={<ManualJournals />} />

          {/* Other */}
          <Route path="/settings" element={<Settings />} />
          <Route path="/help" element={<Help />} />
          <Route path="/contact" element={<ContactSupport />} />
          <Route path="/upgrade" element={<Upgrade />} />

          <Route path="*" element={<Navigate to="/home" replace />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;