import './HeroSection.css';
import Heroimg from 'D:/tally-to-books/src/assets/Hero-img.png';
import Hero from 'D:/tally-to-books/src/assets/hero.png'
const HeroSection = () => (
  <section id="hero" className="hero-section">
    <div className="hero-content">
      <h1>Powerful Features To Simplify Your Migration</h1>
      <p>Move from Tally to Zoho Books with ease and confidence.</p>
      <p>Unlock the full potential of your Accounting with Our Seamless, stress-free Migration services </p>
      <div className="hero-input">
        <input type="email" placeholder="Your email address" />
        <button>Subscribe</button>
      </div>
    </div>
    <div className="hero-image">
      {/* Insert your dashboard screenshot or illustration here */}
      <img src={Hero} className='hero-img' alt="Migration Dashboard"/>
    </div>
  </section>
);

export default HeroSection;