export default function HeroSection({ setCurrentPage }) {
  return (
    <section className="px-4 sm:px-6 pt-10 pb-6 max-w-7xl mx-auto">
      {/* Badge */}
      <div className="inline-flex items-center gap-2 border border-amber text-amber text-[10px] font-mono font-bold uppercase tracking-widest px-3 py-1.5 mb-6">
        <span>NEXT-GEN RAG AI</span>
        <span className="text-zinc-500">◇</span>
        <span>4 VERIFIED SUV BROCHURES</span>
      </div>

      {/* H1 */}
      <h1 className="text-4xl sm:text-5xl lg:text-7xl font-black uppercase leading-none tracking-tight text-white mb-5">
        PRECISION<br />
        AUTOMOTIVE<br />
        INTELLIGENCE.
      </h1>

      {/* Subtitle */}
      <p className="text-zinc-400 text-sm sm:text-base leading-relaxed mb-8 max-w-md">
        Ask complex questions, list variant features, and compare Hyundai Alcazar,
        Hyundai Creta, Kia Seltos, and Tata Nexon with brochure-grounded answers
        and exact page citations.
      </p>

      {/* CTAs */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          className="btn-amber text-xs px-6 py-3"
          onClick={() => setCurrentPage('models')}
        >
          START AI COMPARISON →
        </button>
        <button
          className="btn-outline text-xs px-6 py-3"
          onClick={() => setCurrentPage('models')}
        >
          EXPLORE 4 MODELS
        </button>
      </div>

      {/* Hero car image */}
      <div className="mt-10 w-full overflow-hidden" style={{ maxHeight: '300px' }}>
        <img
          src="https://images.unsplash.com/photo-1620891549027-942fdc95d3f5?w=800&q=80&auto=format&fit=crop"
          alt="Luxury SUV"
          className="w-full object-cover object-center"
          style={{ maxHeight: '300px' }}
          onError={(e) => {
            e.target.src = 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800&q=80';
          }}
        />
      </div>
    </section>
  );
}
