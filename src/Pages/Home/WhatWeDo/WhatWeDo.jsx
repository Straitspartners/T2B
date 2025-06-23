import React from 'react';
import './WhatWeDo.css';
import DataIntegrationImg from 'D:/tally-to-books/src/assets/DataIntegrationImg.png'
import MinimalDowntimeImg from 'D:/tally-to-books/src/assets/MinimalDowntimeImg.png';
import CustomConfigImg from 'D:/tally-to-books/src/assets/CustomConfigImg.png';
import Support from "D:/tally-to-books/src/assets/support.png"
const WhatWeDo = () => {
 const cards = [
  {
    title: "Data Integration",
    text: "We ensure the accurate and secure transfer of your financial data. All historical records and relationships are preserved, so you can count on migration process.",
    image: DataIntegrationImg
  },
  {
    title: "Minimal Downtime",
    text: "We ensure a seamless migration experience, minimizing disruption while preserving the integrity of your operations for a smooth and efficient transition.",
    image: MinimalDowntimeImg
  },
  {
    title: "Custom Configuration",
    text: "We tailor the setup to meet your specific needs. From start to finish, our approach ensures a personalized configuration that aligns perfectly with your business goals.",
    image: CustomConfigImg
  },
  {
    title: "Post-Migration Support",
    text: "We provide continuous support after migration. Whether it’s a question or technical help, our team is ready to assist and ensure everything works as expected with setup.",
    image: Support
  }
];
  return (
    <section id="whatwedo" className="what-section">
      <h2 className='highlight'>What We Do</h2>
      <p className='features-title'>We facilitate seamless data migration from Tally </p>
      <p className='highlight'> <span className='features-title'>to</span> Zoho Books.</p>
    <div className="what-cards">
      
       {cards.map((card, index) => (
        <div className="card" >
        <div className="card-overley" key={index}>
            <h3 className='card-title-wwd'>{card.title}</h3>
          <p className='card-description'>{card.text}</p>
          <img src={card.image} alt={card.title} className="card-image" />
        </div>
        </div>
      ))}
    </div>
    </section>
  );
};

export default WhatWeDo;



// import React from 'react';
// import './WhatWeDo.css';
// import DataIntegrationImg from './images/data-integration.png';
// import MinimalDowntimeImg from './images/minimal-downtime.png';
// import CustomConfigImg from './images/custom-configuration.png';
// import PostMigrationSupportImg from './images/post-migration-support.png';

// const cards = [
//   {
//     title: "Data Integration",
//     text: "We guarantee a precise and secure transfer of your financial data, carefully maintaining all historical records and relationships. You can rely on us to handle your information with exceptional accuracy and attention to detail.",
//     image: DataIntegrationImg
//   },
//   {
//     title: "Minimal Downtime",
//     text: "We ensure a seamless migration experience, minimizing disruption while preserving the integrity of your operations for a smooth and efficient transition.",
//     image: MinimalDowntimeImg
//   },
//   {
//     title: "Custom Configuration",
//     text: "We customize the setup to perfectly align with your unique requirements, guaranteeing a seamless transition that meets all your expectations.",
//     image: CustomConfigImg
//   },
//   {
//     title: "Post-Migration Support",
//     text: "We’re here to assist you with any questions or issues you may encounter after the migration process! Don’t hesitate to reach out for support, as we’re committed to ensuring a smooth transition for you.",
//     image: PostMigrationSupportImg
//   }
// ];

// const WhatWeDo = () => (
//   <section id="whatwedo" className="what-section">
//     <h2 className="highlight">What We Do</h2>
//     <p className="features-title">We facilitate seamless data migration from Tally <span className="highlight">to</span> Zoho Books.</p>
//     <div className="what-cards">
//       {cards.map((card, index) => (
//         <div className="card" key={index}>
//           <img src={card.image} alt={card.title} className="card-image" />
//           <h3>{card.title}</h3>
//           <p>{card.text}</p>
//         </div>
//       ))}
//     </div>
//   </section>
// );

// export default WhatWeDo;
