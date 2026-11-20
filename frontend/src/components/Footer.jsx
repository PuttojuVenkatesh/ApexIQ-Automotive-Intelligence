export default function Footer() {
  return (
    <footer className="bg-[#090a0c] text-white">
      <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12 py-16 grid grid-cols-1 md:grid-cols-3 gap-12">
        <div>
          <div className="text-2xl font-black tracking-[0.18em] mb-5">ApexIQ</div>
          <p className="text-sm text-white/55 max-w-xs leading-7">
            A curated guide to modern SUVs, built around verified specifications and official vehicle information.
          </p>
        </div>
        <div>
          <h3 className="text-xs font-bold uppercase tracking-[0.2em] mb-5">Models</h3>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm text-white/65">
            {['Hyundai Alcazar', 'Hyundai Creta', 'Kia Seltos', 'Tata Nexon'].map((m) => (
              <a key={m} href="#models" className="hover:text-white">{m}</a>
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-xs font-bold uppercase tracking-[0.2em] mb-5">Explore</h3>
          <div className="flex flex-col gap-3 text-sm text-white/65">
            <a href="#models" className="hover:text-white">Discover Models</a>
            <a href="#compare" className="hover:text-white">Compare Vehicles</a>
            <a href="#models" className="hover:text-white">View Features</a>
            <a href="#admin" className="hover:text-white">Brochure Administration</a>
          </div>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12 py-6 text-xs text-white/40 flex flex-col sm:flex-row justify-between gap-2">
          <span>© 2026 ApexIQ. All rights reserved.</span>
          <span>Specifications subject to change by the manufacturer.</span>
        </div>
      </div>
    </footer>
  );
}
