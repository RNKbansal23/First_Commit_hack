import React, { useState, useEffect, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Stars } from '@react-three/drei';
import { motion, AnimatePresence } from 'framer-motion';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Briefcase, Building, MapPin, ExternalLink, Activity, Clock, Search, Filter, X } from 'lucide-react';
import './App.css';

gsap.registerPlugin(ScrollTrigger);

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
    card.style.transform = "perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)";
  };
  const handleMouseLeave = () => {
    const card = cardRef.current;
    if(card) card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)";
  };
  
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
          {job.is_new && <span className="new-badge">?? JUST POSTED</span>}
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
          <span className="platform-tag ml-2"><Clock size={10} className="inline mr-1" /> {new Date(job.posted_at + 'Z').toLocaleString()}</span>
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
  const [activeTab, setActiveTab] = useState('jobs');
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
    let url = new URL('http://127.0.0.1:5000/api/jobs');
    
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
    fetchJobs(activeFilters, {
      region: selectedRegion,
      posted_since: selectedPosted,
      experience_max: selectedExp
    });
  }, [activeFilters, selectedRegion, selectedPosted, selectedExp]);

  const handleSmartSearch = async (e) => {
    e.preventDefault();
    if(!searchQuery.trim()) {
      setActiveFilters({});
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:5000/api/jobs/smart-search', {
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
