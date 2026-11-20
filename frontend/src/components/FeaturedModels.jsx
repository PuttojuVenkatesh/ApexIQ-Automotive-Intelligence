// Featured Comparison Card + Vehicle Lineup section
const CARS = [
  {
    name: 'Hyundai Alcazar',
    price: '₹16.77L+',
    spec: '6/7-Seater · 1.5L Turbo GDi (160 PS) · Level 2 ADAS',
    slug: 'ALCAZAR',
    img: 'https://images.unsplash.com/photo-1550355291-bbee04a92027?w=600&q=80&auto=format&fit=crop',
  },
  {
    name: 'Hyundai Creta',
    price: '₹11.00L+',
    spec: '5-Seater · 433L Boot · Panoramic Sunroof',
    slug: 'CRETA',
    img: 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=600&q=80&auto=format&fit=crop',
  },
  {
    name: 'Kia Seltos',
    price: '₹10.90L+',
    spec: '5-Seater · 1.5L T-GDi (160 PS) · Dual 10.25" Display',
    slug: 'SELTOS',
    img: 'https://images.unsplash.com/photo-1612825173281-9a193378527e?w=600&q=80&auto=format&fit=crop',
  },
  {
    name: 'Tata Nexon',
    price: '₹8.00L+',
    spec: '5-Star GNCAP · 382L Boot · 360° Blind View Monitor',
    slug: 'NEXON',
    img: 'https://images.unsplash.com/photo-1617469767053-d3b523a0b982?w=600&q=80&auto=format&fit=crop',
  },
];

const CAR_IMAGES = [
  // Dark studio SUV shots from Unsplash
  'https://images.unsplash.com/photo-1620891549027-942fdc95d3f5?w=600&q=80&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=600&q=80&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1612825173281-9a193378527e?w=600&q=80&auto=format&fit=crop',
  'https://images.unsplash.com/photo-1617469767053-d3b523a0b982?w=600&q=80&auto=format&fit=crop',
];

export default function FeaturedModels({ setCurrentPage }) {
  return (
    <>
      {/* ── Featured Comparison Card ── */}
      <section className="px-4 sm:px-6 pb-10 max-w-7xl mx-auto">
        <div
          className="card p-5"
          style={{ borderColor: '#1e2435' }}
        >
          <div className="section-label mb-2">FEATURED COMPARISON</div>
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <h2 className="text-xl font-black text-white">
              Hyundai Alcazar vs. Creta
            </h2>
            <span className="rag-badge text-xs px-3 py-1 bg-black/30 border border-green-rag/30 font-mono">
              pgvector · 0.94 match
            </span>
          </div>
        </div>
      </section>

      {/* ── Indexed Vehicle Lineup ── */}
      <section className="px-4 sm:px-6 pb-16 max-w-7xl mx-auto">
        <div className="section-label mb-2" style={{ color: '#f97316' }}>INDEXED VEHICLE LINEUP</div>
        <h2 className="text-3xl sm:text-4xl font-black text-white uppercase leading-none mb-3">
          FOUR SUVS. EVERY<br className="sm:hidden" /> VARIANT.
        </h2>
        <p className="text-zinc-400 text-sm mb-8 max-w-lg">
          All specifications are extracted directly from official PDF brochures
          uploaded via the Admin Console.
        </p>

        {/* Car cards — stacked on mobile, 2-col on sm+ */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-0 divide-y sm:divide-y-0 divide-border">
          {CARS.map((car, i) => (
            <CarCard key={car.name} car={car} img={CAR_IMAGES[i]} setCurrentPage={setCurrentPage} />
          ))}
        </div>
      </section>
    </>
  );
}

function CarCard({ car, img, setCurrentPage }) {
  return (
    <div className="bg-surface border border-border overflow-hidden group">
      {/* Car image */}
      <div className="relative overflow-hidden" style={{ height: '220px' }}>
        <img
          src={img}
          alt={car.name}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          onError={(e) => {
            e.target.style.display = 'none';
            e.target.parentNode.style.background = '#13161f';
          }}
        />
        {/* Gradient overlay */}
        <div
          className="absolute inset-0"
          style={{ background: 'linear-gradient(to top, #13161f 0%, transparent 60%)' }}
        />
      </div>

      {/* Info */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-lg font-black text-white">{car.name}</h3>
          <span className="text-amber font-mono font-bold text-sm">{car.price}</span>
        </div>
        <p className="text-zinc-400 text-xs mb-4">{car.spec}</p>

        <button
          onClick={() => setCurrentPage('models')}
          className="flex items-center gap-2 text-amber text-xs font-bold uppercase tracking-widest group-hover:gap-3 transition-all duration-200"
        >
          COMPARE {car.slug} <span>→</span>
        </button>
      </div>
    </div>
  );
}
