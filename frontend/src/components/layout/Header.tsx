import { Link } from "react-router-dom";
import { UserButton } from "@clerk/clerk-react";

export default function Header() {
  return (
    <header className="main-header">
      <div className="logo-title">
        <Link to="/" className="logo-title" style={{ textDecoration: 'none', color: 'inherit' }}>
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary" style={{ filter: 'drop-shadow(0 2px 8px rgba(0,123,255,0.10))' }}>
            <span className="text-xl font-bold text-white">C</span>
          </div>
          <h1>Capstone 2025</h1>
        </Link>
      </div>
      <div className="header-actions">
        <Link
          to="/create-project"
          className="create-project-cta"
          style={{ textDecoration: 'none' }}
        >
          Start a New Project
        </Link>
        <UserButton />
      </div>
    </header>
  );
}

