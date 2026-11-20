import { useEffect, useState } from 'react';
import Navbar from './components/Navbar';
import VehicleCatalogPage from './pages/VehicleCatalogPage';
import ChatWidget from './components/ChatWidget';
import BrochureAdminSection from './components/BrochureAdminSection';

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  const [adminPage, setAdminPage] = useState(window.location.hash === '#admin');

  useEffect(() => {
    const syncPage = () => setAdminPage(window.location.hash === '#admin');
    window.addEventListener('hashchange', syncPage);
    return () => window.removeEventListener('hashchange', syncPage);
  }, []);

  return (
    <div className="min-h-screen">
      <Navbar onOpenChat={() => setChatOpen(true)} />
      {adminPage
        ? <BrochureAdminSection />
        : <VehicleCatalogPage onOpenChat={() => setChatOpen(true)} />}
      {!adminPage && <ChatWidget isOpen={chatOpen} onClose={() => setChatOpen(false)} />}
    </div>
  );
}
