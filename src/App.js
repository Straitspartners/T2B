import './App.css';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Signin from './Auth/Signin';
import Nav from './components/Nav/Navigation';
import Herosection from './Pages/Home/HeroSection/HeroSection';
import Services from './Pages/Home/Services/Services';
import Whatwedo from './Pages/Home/WhatWeDo/WhatWeDo';
import Migration from './Pages/Home/MigrationProcess/MigrationProcess';
import Contact from './Pages/Home/Contact/Contact';
import Faq from './Pages/Home/FAQ/FAQ';
import Footer from './Pages/Home/Footer/Footer';
import Setup from './Pages/Home/Setup/Setup';
import Dashboard from './Pages/Home/Dashboard/Dashboard';
import Masters from './Pages/Home/Dashboard/Masters';
import Transactions from './Pages/Home/Dashboard/Transactions';
import Help from './Pages/Home/Dashboard/Help';       
import ContactSupport from './Pages/Home/Dashboard/ContactSupport'; 
import Settings from './Pages/Home/Dashboard/Settings';
import Upgrade from './Pages/Home/Dashboard/Upgrade'; // Assuming Upgrade is a page similar to Help and ContactSupport
import QuickMigration from './Pages/Home/Dashboard/QuickMigration'; // Importing the QuickMigration component
import Customers from './Pages/Home/Dashboard/Customers'; // Importing the Customers component
import Vendors from './Pages/Home/Dashboard/Vendors'; // Importing the Vendors component
import Chartofaccounts from './Pages/Home/Dashboard/ChartofAC'; 
import Items from './Pages/Home/Dashboard/Item';
import Invoice from './Pages/Home/Dashboard/Invoice';
import PaymentReceived from './Pages/Home/Dashboard/PaymentReceived';
import Sidebar from './components/Sidebar';
import Signup from './Auth/Signup';

// Home page with Nav and Footer
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
          <Route path="/" element={<HomePage />} />
          <Route path="/home" element={<HomePage />} />
          <Route path="/signin" element={<Signin />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/setup" element={<Setup />} />

          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/sidebar" element={<Sidebar  />} />
          <Route path="/masters" element={<Masters />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/help" element={<Help />} />
          <Route path="/contact" element={<ContactSupport />} />
          <Route path="/upgrade" element={<Upgrade />} />
          <Route path="/quick-migration" element={<QuickMigration />} /> {/* Route for QuickMigration */}
          <Route path="/customers" element={<Customers />} />
          <Route path="/vendors" element={<Vendors />} />
          <Route path="/chart-of-accounts" element={<Chartofaccounts />} /> {/* Route for Chart of Accounts */}
          <Route path="/items" element={<Items />} /> {/* Route for Items */}
          <Route path="/invoice" element={<Invoice />} /> {/* Route for Invoice */}
          <Route path="/payment-received" element={<PaymentReceived />} /> {/* Route for Payment Received */}
          <Route path="*" element={<Navigate to="/home" replace />} />
          {/* Nested routes for Masters and Transactions */}
          {/* Add more routes as needed */}
        </Routes>
      </Router>
    </div>
  );
}

export default App;
