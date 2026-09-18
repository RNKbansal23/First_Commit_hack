import React, { useState, useRef, useEffect } from 'react';
import './App.css';

// The custom 3D Tilt Card Component
const TiltCard = ({ job }) => {
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {
    const card = cardRef.current;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const rotateY = -15 + (x / rect.width) * 30;
    const rotateX = 15 - (y / rect.height) * 30;

    card.style.transform = "perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.05)";
  };

  const handleMouseLeave = () => {
    const card = cardRef.current;
    card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)";
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
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/jobs')
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        setJobs(data.jobs_array || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Fetch error:", err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>FirstMover <span className="highlight">Live</span></h1>
        <p>True Fresher roles, found 48 hours before the crowd.</p>
      </header>

      {loading && <div style={{textAlign: 'center', marginTop: '50px'}}>Loading live jobs... 🚀</div>}
      {error && <div style={{textAlign: 'center', marginTop: '50px', color: '#ef4444'}}>Error fetching jobs: {error}</div>}

      {!loading && !error && (
        <div className="jobs-grid">
          {jobs.map(job => (
            <TiltCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}
