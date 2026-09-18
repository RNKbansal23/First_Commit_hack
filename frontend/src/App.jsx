import React, { useState, useRef } from 'react';
import './App.css';

// The custom 3D Tilt Card Component
const TiltCard = ({ job }) => {
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {
    const card = cardRef.current;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left; // x position within the element
    const y = e.clientY - rect.top;  // y position within the element
    
    // Calculate rotation limits (-15 to +15 degrees)
    const rotateY = -15 + (x / rect.width) * 30;
    const rotateX = 15 - (y / rect.height) * 30;

    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.05)`;
  };

  const handleMouseLeave = () => {
    const card = cardRef.current;
    card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)`;
  };

  return (
    <div 
      className="parallax-effect" 
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div className="inner-card">
        <div className="company-badge">{job.company}</div>
        <h3 className="job-title">{job.title}</h3>
        <p className="job-location">📍 {job.location}</p>
        
        <div className="card-actions">
          <button className="apply-btn" onClick={() => window.open(job.url, '_blank')}>
            Apply Now
          </button>
          <button className="referral-btn">
            Draft Referral
          </button>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  // Test data based on your successful Python scraper output
  const demoJobs = [
    { id: '1', company: 'Figma', title: 'Brand Design Intern (Summer 2027)', location: 'Remote', url: '#' },
    { id: '2', company: 'Figma', title: 'Data Science Intern (2027)', location: 'Remote', url: '#' },
    { id: '3', company: 'Figma', title: 'Director, People Partners - Product, Design & Engineering', location: 'Remote', url: '#' }
  ];

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>FirstMover <span className="highlight">Live</span></h1>
        <p>True Fresher roles, found 48 hours before the crowd.</p>
      </header>

      <div className="jobs-grid">
        {demoJobs.map(job => (
          <TiltCard key={job.id} job={job} />
        ))}
      </div>
    </div>
  );
}