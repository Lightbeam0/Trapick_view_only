// src/components/Sidebar.js - REMOVED UPLOAD MODAL AND SETTINGS
import React from "react";
import { Link, useLocation } from "react-router-dom";
import { FaChartLine, FaCarSide, FaTrafficLight, FaMagic, FaMapMarkerAlt } from "react-icons/fa";

function Sidebar() {
  const location = useLocation();

  const menuItems = [
    { path: "/", label: "Overview", icon: <FaChartLine /> },
    { path: "/vehicles", label: "Vehicles Passing", icon: <FaCarSide /> },
    { path: "/congested", label: "Congested Roads", icon: <FaTrafficLight /> },
    { path: "/locations", label: "Locations", icon: <FaMapMarkerAlt /> },
    { path: "/predictions", label: "Traffic Predictions", icon: <FaMagic /> },
  ];  

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>Traffic Monitor</h1>
        <p>Zamboanga City</p>
      </div>

      <nav className="sidebar-nav">
        <ul className="sidebar-nav-list">
          {menuItems.map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={`sidebar-nav-link ${location.pathname === item.path ? 'active' : ''}`}
              >
                <span className="sidebar-nav-icon">{item.icon}</span>
                <span>{item.label}</span>
                {location.pathname === item.path && (
                  <span style={{ marginLeft: 'auto', width: '8px', height: '8px', backgroundColor: 'white', borderRadius: '50%' }}></span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <p></p>
        <p style={{ marginTop: '4px' }}></p>
      </div>
    </div>
  );
}

export default Sidebar;