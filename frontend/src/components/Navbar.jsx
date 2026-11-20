export default function Navbar({ onOpenChat }) {
  return (
    <nav className="fixed top-0 z-50 w-full text-white" style={{ background: 'linear-gradient(180deg,rgba(7,8,10,.94),rgba(7,8,10,.72))', backdropFilter: 'blur(14px)' }}>
      <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12 h-20 flex items-center justify-between">
        <a href="#" className="text-xl sm:text-2xl font-black tracking-[0.18em]" aria-label="ApexIQ home">
          ApexIQ
        </a>
        <div className="hidden md:flex items-center gap-9 text-xs font-semibold uppercase tracking-[0.16em]">
          <a href="#models" className="nav-link">Models</a>
          <a href="#compare" className="nav-link">Compare</a>
          <a href="#safety" className="nav-link">Safety</a>
          <a href="#ownership" className="nav-link">Ownership</a>
        </div>
        <div className="flex items-center gap-2 sm:gap-4">
          <a
            href="#admin"
            className="border border-white/30 px-3 sm:px-4 py-3 text-[10px] sm:text-xs font-bold uppercase tracking-[0.14em] text-white/75 hover:border-white hover:text-white transition-colors"
          >
            Admin
          </a>
          <button onClick={onOpenChat} className="border border-white/50 px-4 sm:px-6 py-3 text-[10px] sm:text-xs font-bold uppercase tracking-[0.18em] hover:bg-white hover:text-black transition-colors">
            GearGuide
          </button>
        </div>
      </div>
    </nav>
  );
}
