import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Signin from './Auth/Signin';
import Nav from './Pages/Home/Nav/Navigation';
import Herosection from './Pages/Home/HeroSection/HeroSection';
import Services from './Pages/Home/Services/Services';
import Whatwedo from './Pages/Home/WhatWeDo/WhatWeDo';
import Migration from './Pages/Home/MigrationProcess/MigrationProcess';
import Contact from './Pages/Home/Contact/Contact';
import Faq from './Pages/Home/FAQ/FAQ';
import Footer from './Pages/Home/Footer/Footer';

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
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/signin" element={<Signin />} />
          <Route path="*" element={<div>Page Not Found</div>} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;