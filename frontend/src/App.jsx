import React, { useState, useEffect, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Stars } from '@react-three/drei';
import { motion } from 'framer-motion';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Briefcase, Building, MapPin, ExternalLink, Activity, Clock } from 'lucide-react';
import './App.css';

gsap.registerPlugin(ScrollTrigger);

// 3D Hero Element
const HeroScene = () => {
  const group = useRef();
  
  useFrame(({ clock, mouse }) => {
    if (group.current) {
      group.current.rotation.y = clock.getElapsedTime() * 0.05 + (mouse.x * 0.1);
      group.current.rotation.x = (mouse.y * 0.1);
    }
  });

  return (
    <group ref={group}>
      <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
      <mesh>
        <sphereGeometry args={[1.5, 64, 64]} />
        <meshStandardMaterial color="#3b82f6" wireframe opacity={0.3} transparent />
      </mesh>
    </group>
  );
};

// Job Card with Framer Motion and Tilt
const JobCard = ({ job, index }) => {
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {
    const card = cardRef.current;
    if(!card) return;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const rotateY = -10 + (x / rect.width) * 20;
    const rotateX = 10 - (y / rect.height) * 20;

    card.style.transform = "perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)";
  };

  const handleMouseLeave = () => {
    const card = cardRef.current;
    if(card) card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="parallax-effect" 
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div className="inner-card">
        <div className="card-header">
          <div className="company-badge">
            <Building size={14} className="mr-1" />
            {job.company}
          </div>
          {job.is_new && <span className="new-badge">🔥 JUST POSTED</span>}
        </div>
        
        <h3 className="job-title">{job.title}</h3>
        <p className="job-location">
          <MapPin size={14} className="mr-1" />
          {job.location}
        </p>
        
        <div className="card-footer">
          <span className="platform-tag">{job.source_platform}</span>
        </div>

        <div className="card-actions">
          <button className="apply-btn" onClick={() => window.open(job.url, '_blank')}>
            Apply Now <ExternalLink size={14} className="ml-1" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

// Drive Card
const DriveCard = ({ drive, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.1 }}
      className="drive-card"
    >
      <div className="drive-header">
        <h3>{drive.company}</h3>
        <span className="status-badge">{drive.status}</span>
      </div>
      <h2>{drive.exam_name}</h2>
      <div className="drive-details">
        <p><Clock size={14} /> Closes: {drive.registration_closes_at}</p>
        <p><Briefcase size={14} /> Eligibility: {drive.eligibility_criteria}</p>
      </div>
      <button className="apply-btn w-full mt-4" onClick={() => window.open(drive.source_url, '_blank')}>
        Register Now
      </button>
    </motion.div>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState('jobs');
  const [jobs, setJobs] = useState([]);
  const [drives, setDrives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [companyFilter, setCompanyFilter] = useState('All');
  
  const containerRef = useRef();

  const fetchJobs = () => {
    setLoading(true);
    fetch('http://127.0.0.1:5000/api/jobs')
      .then(res => res.json())
      .then(data => {
        setJobs(data.jobs_array || []);
        setLoading(false);
      });
  };

  const fetchDrives = () => {
    fetch('http://127.0.0.1:5000/api/drives')
      .then(res => res.json())
      .then(data => setDrives(data.drives || []));
  };

  useEffect(() => {
    fetchJobs();
    fetchDrives();
  }, []);

  useEffect(() => {
    // GSAP ScrollTrigger for sections
    const sections = document.querySelectorAll('.fade-in-section');
    sections.forEach(sec => {
      gsap.fromTo(sec, 
        { opacity: 0, y: 50 },
        { 
          opacity: 1, y: 0, 
          duration: 0.8, 
          scrollTrigger: {
            trigger: sec,
            start: "top 80%",
          }
        }
      );
    });
  }, [loading, activeTab]);

  const companies = ['All', ...new Set(jobs.map(j => j.company))];
  const filteredJobs = companyFilter === 'All' ? jobs : jobs.filter(j => j.company === companyFilter);

  return (
    <div className="app-wrapper" ref={containerRef}>
      {/* 3D Hero Section */}
      <div className="hero-section">
        <div className="canvas-container">
          <Canvas camera={{ position: [0, 0, 5] }}>
            <ambientLight intensity={0.5} />
            <pointLight position={[10, 10, 10]} />
            <HeroScene />
          </Canvas>
        </div>
        <div className="hero-content">
          <motion.h1 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
          >
            JobPulse <span className="highlight">Aggregator</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            Directly indexing ATS endpoints for top 20 tech giants. Bypassing generic boards.
          </motion.p>
        </div>
      </div>

      <div className="dashboard-container fade-in-section">
        
        {/* Navigation Tabs */}
        <div className="tabs">
          <button 
            className={"tab-btn "} 
            onClick={() => setActiveTab('jobs')}
          >
            Live Openings
          </button>
          <button 
            className={"tab-btn "} 
            onClick={() => setActiveTab('drives')}
          >
            Upcoming IT Drives
          </button>
          <button 
            className="tab-btn admin-btn"
            onClick={() => window.open('http://127.0.0.1:5000/admin/connector-status', '_blank')}
          >
            <Activity size={16} className="mr-2"/> Status
          </button>
        </div>

        {activeTab === 'jobs' && (
          <>
            {/* Company Filter Chips */}
            <div className="filter-chips">
              {companies.map(c => (
                <button 
                  key={c}
                  className={"chip "}
                  onClick={() => setCompanyFilter(c)}
                >
                  {c}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="loader">Syncing Connectors...</div>
            ) : (
              <div className="jobs-grid">
                {filteredJobs.map((job, idx) => (
                  <JobCard key={job.id} job={job} index={idx} />
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'drives' && (
          <div className="drives-grid fade-in-section">
            {drives.length === 0 ? (
              <div className="loader">No active drives tracked at the moment.</div>
            ) : (
              drives.map((drive, idx) => (
                <DriveCard key={drive.id} drive={drive} index={idx} />
              ))
            )}
          </div>
        )}

      </div>
    </div>
  );
}
