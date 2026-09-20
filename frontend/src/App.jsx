import React, { useState, useEffect, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Stars } from '@react-three/drei';
import { motion, AnimatePresence } from 'framer-motion';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Briefcase, Building, MapPin, ExternalLink, Activity, Clock, Search, Filter, X, Bell } from 'lucide-react';

import toast, { Toaster } from 'react-hot-toast';
import './App.css';

gsap.registerPlugin(ScrollTrigger);

const formatRelativeTime = (timestamp) => {
  if (!timestamp) return '';
  const now = new Date();
  const past = new Date(timestamp.endsWith('Z') ? timestamp : timestamp + 'Z');
  const diffInSeconds = Math.floor((now - past) / 1000);
  
  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
  
  return past.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const useRelativeTime = (timestamp) => {
  const [timeStr, setTimeStr] = useState(formatRelativeTime(timestamp));
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeStr(formatRelativeTime(timestamp));
    }, 30000);
    return () => clearInterval(interval);
  }, [timestamp]);
  return timeStr;
};

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
        <sphereGeometry args={[2.5, 64, 64]} />
        <meshStandardMaterial color="#3b82f6" wireframe opacity={0.3} transparent />
      </mesh>
    </group>
  );
};

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
    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
  };
  const handleMouseLeave = () => {
    const card = cardRef.current;
    if(card) card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)";
  };
  
  const relativeTime = useRelativeTime(job.posted_at);
  const isNew = relativeTime === 'Just now' || relativeTime.includes('minutes ago') && parseInt(relativeTime) < 5;
  let parsedSkills = [];
  try { if(job.skills) parsedSkills = JSON.parse(job.skills); } catch(e){}

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.3 }}
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
          {isNew && <span className="new-badge pulse">🔥 NEW</span>}
        </div>
        
        <h3 className="job-title">{job.title}</h3>
        <p className="job-location">
          <MapPin size={14} className="mr-1" />
          {job.location} {job.work_mode ? '(' + job.work_mode + ')' : ''}
        </p>
        
        {parsedSkills.length > 0 && (
          <div className="skills-row">
            {parsedSkills.map(s => <span key={s} className="skill-tag">{s}</span>)}
          </div>
        )}
        
        <div className="card-footer">
          <span className="platform-tag">{job.source_platform}</span>
          <span className="platform-tag ml-2">{job.region}</span>
          <span className="platform-tag ml-2">
            <Clock size={10} className="inline mr-1" /> {relativeTime}
          </span>
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

export default function App() {
  const [notifications, setNotifications] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const unreadCount = notifications.filter(n => !n.read).length;

  useEffect(() => {
    
    return () => socket.disconnect();
  }, []);


  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Filters
  const [companyFilter, setCompanyFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilters, setActiveFilters] = useState({});
  
  // Explicit UI Dropdown States
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedPosted, setSelectedPosted] = useState('');
  const [selectedExp, setSelectedExp] = useState('');

  const fetchJobs = (filters = {}, explicit = {}) => {
    setLoading(true);
    let url = new URL('https://REPLACE_WITH_YOUR_API_GATEWAY_URL/Prod/api/jobs');
    
    // AI Filters
    if (filters['experience_max']) url.searchParams.append('experience_max', filters['experience_max']);
    if (filters['title_match']) url.searchParams.append('title_match', filters['title_match']);
    if (filters['skills[]']) {
      filters['skills[]'].forEach(s => url.searchParams.append('skills[]', s));
    }
    if (filters['work_mode[]']) {
      filters['work_mode[]'].forEach(w => url.searchParams.append('work_mode[]', w));
    }
    
    // Explicit UI Filters (overrides)
    if (explicit.region) url.searchParams.append('region', explicit.region);
    if (explicit.posted_since) url.searchParams.append('posted_since', explicit.posted_since);
    if (explicit.experience_max) url.searchParams.append('experience_max', explicit.experience_max);

    fetch(url)
      .then(res => res.json())
      .then(data => {
        setJobs(data.jobs_array || []);
        setLoading(false);
      });
  };

  useEffect(() => {
    const interval = setInterval(() => fetchJobs(activeFilters, { region: selectedRegion, posted_since: selectedPosted, experience_max: selectedExp }), 5000);
    setTimeout(() => fetchJobs(activeFilters, {

      region: selectedRegion,
      posted_since: selectedPosted,
      experience_max: selectedExp
    }), 0);
  return () => clearInterval(interval);
  }, [activeFilters, selectedRegion, selectedPosted, selectedExp]);

  const handleSmartSearch = async (e) => {
    e.preventDefault();
    if(!searchQuery.trim()) {
      setActiveFilters({});
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('https://REPLACE_WITH_YOUR_API_GATEWAY_URL/Prod/api/jobs/smart-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery })
      });
      const data = await res.json();
      setActiveFilters(data.parsed_filters || {});
    } catch(err) {
      console.error(err);
      setLoading(false);
    }
  };

  const removeFilter = (key) => {
    const newF = {...activeFilters};
    delete newF[key];
    setActiveFilters(newF);
  };

  const companies = ['All', ...new Set(jobs.map(j => j.company))];
  const filteredJobs = companyFilter === 'All' ? jobs : jobs.filter(j => j.company === companyFilter);

  return (
    <div className="app-wrapper">
      <Toaster />
      
      {/* Top Nav Notification Bell */}
      <div style={{ position: 'fixed', top: 20, right: 30, zIndex: 1000 }}>
        <div style={{ position: 'relative' }}>
          <button 
            onClick={() => setShowDropdown(!showDropdown)}
            style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '50%', color: 'white', cursor: 'pointer', pointerEvents: 'auto' }}
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span style={{ position: 'absolute', top: -5, right: -5, background: 'red', color: 'white', borderRadius: '50%', padding: '2px 6px', fontSize: '10px', fontWeight: 'bold' }}>
                {unreadCount}
              </span>
            )}
          </button>
          
          {showDropdown && (
            <div style={{ position: 'absolute', top: 50, right: 0, width: 300, background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '10px', color: 'white', backdropFilter: 'blur(10px)', pointerEvents: 'auto', maxHeight: '400px', overflowY: 'auto' }}>
              <h3 style={{ margin: '0 0 10px 0', fontSize: '14px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '10px' }}>Notifications</h3>
              {notifications.length === 0 ? (
                <p style={{ fontSize: '12px', color: '#94a3b8' }}>No new notifications.</p>
              ) : (
                notifications.map((n, i) => (
                  <div key={i} style={{ padding: '10px', borderBottom: '1px solid rgba(255,255,255,0.05)', cursor: 'pointer' }} onClick={() => window.open(n.job.url, '_blank')}>
                    <div style={{ fontWeight: 'bold', fontSize: '13px' }}>{n.job.title}</div>
                    <div style={{ fontSize: '12px', color: '#94a3b8' }}>{n.job.company}</div>
                    <div style={{ fontSize: '11px', color: '#3b82f6', marginTop: '5px' }}>{formatRelativeTime(n.job.posted_at)}</div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
      <div className="canvas-container-full">
        <Canvas camera={{ position: [0, 0, 5] }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />
          <HeroScene />
        </Canvas>
      </div>

      <div className="hero-section" style={{height: '35vh'}}>
        <div className="hero-content">
          <motion.h1 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
            JobPulse <span className="highlight">Smart Filters</span>
          </motion.h1>
          
          <form className="search-form" onSubmit={handleSmartSearch}>
            <Search size={20} className="search-icon" />
            <input 
              type="text" 
              placeholder="e.g. backend python roles in remote" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="smart-search-input"
            />
            <button type="submit" className="search-btn">Search AI</button>
          </form>
          
          <div className="explicit-filters">
            <select className="dropdown-filter" value={selectedRegion} onChange={e => setSelectedRegion(e.target.value)}>
              <option value="">Any Country/Region</option>
              <option value="India">India</option>
              <option value="US">United States</option>
              <option value="Remote">Remote</option>
            </select>
            
            <select className="dropdown-filter" value={selectedPosted} onChange={e => setSelectedPosted(e.target.value)}>
              <option value="">Any Time</option>
              <option value="5">Past 5 hours</option>
              <option value="10">Past 10 hours</option>
              <option value="24">Past 24 hours</option>
              <option value="48">Past 2 days</option>
              <option value="168">Past 1 week</option>
            </select>
            
            <select className="dropdown-filter" value={selectedExp} onChange={e => setSelectedExp(e.target.value)}>
              <option value="">Any Experience</option>
              <option value="0">Fresher (0 Years)</option>
              <option value="2">Junior (0-2 Years)</option>
              <option value="5">Mid (3-5 Years)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="dashboard-container">
        {/* Active Filter Chips */}
        {Object.keys(activeFilters).length > 0 && (
          <div className="active-filters">
            <span className="text-sm text-gray-400 mr-2">Smart AI Filters Applied:</span>
            {Object.entries(activeFilters).map(([k, v]) => (
              <div key={k} className="active-chip">
                {k.replace('[]','')} = {Array.isArray(v) ? v.join(',') : v}
                <button onClick={() => removeFilter(k)}><X size={12}/></button>
              </div>
            ))}
            <button className="clear-all" onClick={() => {setActiveFilters({}); setSearchQuery('');}}>Clear All</button>
          </div>
        )}

        <div className="main-layout">
          <div className="feed-area w-full">
            <div className="filter-chips">
              {companies.map(c => (
                <button key={c} className={"chip "} onClick={() => setCompanyFilter(c)}>
                  {c}
                </button>
              ))}
            </div>

            {loading ? (
              <div className="loader">Running Extractor...</div>
            ) : (
              <div className="jobs-grid">
                <AnimatePresence>
                  {filteredJobs.map((job, idx) => (
                    <JobCard key={job.id} job={job} index={idx} />
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}









