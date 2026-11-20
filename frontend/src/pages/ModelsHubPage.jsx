import { useState } from 'react';
import Footer from '../components/Footer';

const MODELS = [
  {
    name: 'Hyundai Alcazar',
    brand: 'Hyundai',
    price: '₹16.77L – ₹21.55L',
    desc: 'Three-row flagship SUV with 6/7-seat configurations, ventilated 2nd-row captain seats, and 1.5L Turbo GDi powertrain.',
    stats: [
      { label: 'POWER', value: '160 PS', color: 'white' },
      { label: 'ADAS', value: 'Level 2 (19)', color: 'orange' },
      { label: 'CHUNKS', value: '142 indexed', color: 'orange' },
    ],
    file: 'Hyundai_Alcazar_2024.pdf',
    img: 'https://images.unsplash.com/photo-1620891549027-942fdc95d3f5?w=700&q=80&auto=format&fit=crop',
  },
  {
    name: 'Hyundai Creta',
    brand: 'Hyundai',
    price: '₹11.00L – ₹20.15L',
    desc: '5-seater midsize benchmark featuring dual 10.25" panoramic displays, Bose 8-speaker audio, and SmartSense Level 2 ADAS.',
    stats: [
      { label: 'POWER', value: '160 PS', color: 'white' },
      { label: 'BOOT', value: '433 L', color: 'white' },
      { label: 'CHUNKS', value: '118 indexed', color: 'orange' },
    ],
    file: 'Hyundai_Creta_Spec.pdf',
    img: 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=700&q=80&auto=format&fit=crop',
  },
  {
    name: 'Kia Seltos',
    brand: 'Kia',
    price: '₹10.90L – ₹20.35L',
    desc: 'Sporty 5-seater with 1.5L T-GDi engine, 7-speed DCT, 17-feature Level 2 ADAS, and dual-zone automatic climate control.',
    stats: [
      { label: 'POWER', value: '160 PS', color: 'white' },
      { label: 'ADAS', value: 'Level 2 (17)', color: 'orange' },
      { label: 'CHUNKS', value: '126 indexed', color: 'orange' },
    ],
    file: 'Kia_Seltos_Brochure.pdf',
    img: 'https://images.unsplash.com/photo-1612825173281-9a193378527e?w=700&q=80&auto=format&fit=crop',
  },
  {
    name: 'Tata Nexon',
    brand: 'Tata',
    price: '₹8.00L – ₹15.50L',
    desc: '5-Star Global NCAP rated compact SUV with 6 airbags standard, 360° surround view, and JBL 9-speaker audio system.',
    stats: [
      { label: 'SAFETY', value: '5-Star GNCAP', color: 'white' },
      { label: 'BOOT', value: '382 L', color: 'white' },
      { label: 'CHUNKS', value: '94 indexed', color: 'orange' },
    ],
    file: 'Tata_Nexon_2024.pdf',
    img: 'https://images.unsplash.com/photo-1617469767053-d3b523a0b982?w=700&q=80&auto=format&fit=crop',
  },
];

const FILTERS = ['All Brands (4)', 'Hyundai (2)', 'Kia (1)', 'Tata (1)'];

export default function ModelsHubPage() {
  const [activeFilter, setActiveFilter] = useState('All Brands (4)');

  const filtered = MODELS.filter((m) => {
    if (activeFilter === 'All Brands (4)') return true;
    return activeFilter.toLowerCase().startsWith(m.brand.toLowerCase());
  });

  return (
    <div>
      {/* Page header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-8 pb-6">
        <div
          className="text-xs font-mono font-bold uppercase tracking-[0.2em] mb-2"
          style={{ color: '#f97316' }}
        >
          VEHICLE DOSSIER &amp; BROCHURE SUMMARIES
        </div>
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white uppercase leading-none">
            MODELS &amp; AI KNOWLEDGE HUB
          </h1>

          {/* Filter tabs */}
          <div className="flex flex-wrap gap-2">
            {FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f)}
                className={`text-xs font-bold uppercase tracking-widest px-4 py-2 border transition-all duration-150 ${
                  activeFilter === f
                    ? 'bg-amber text-black border-amber'
                    : 'border-border text-zinc-400 hover:border-zinc-500 hover:text-white bg-transparent'
                }`}
                style={
                  activeFilter === f
                    ? {
                        clipPath:
                          'polygon(6px 0%,100% 0%,100% calc(100% - 6px),calc(100% - 6px) 100%,0% 100%,0% 6px)',
                      }
                    : {}
                }
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-border mb-6" />

      {/* 2-column grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filtered.map((model) => (
            <ModelCard key={model.name} model={model} />
          ))}
        </div>
      </div>

      <Footer />
    </div>
  );
}

function ModelCard({ model }) {
  return (
    <div className="bg-surface border border-border overflow-hidden flex flex-col group">
      {/* Car image */}
      <div className="relative overflow-hidden" style={{ height: '220px' }}>
        <img
          src={model.img}
          alt={model.name}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          onError={(e) => {
            e.target.style.display = 'none';
            e.target.parentNode.style.background = '#161b2a';
          }}
        />
        {/* Bottom gradient */}
        <div
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(to top, #13161f 0%, transparent 60%)',
          }}
        />
      </div>

      {/* Content */}
      <div className="p-5 flex flex-col flex-1">
        {/* Name + Price */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <h2 className="text-xl font-black text-white leading-tight">{model.name}</h2>
          <span className="text-amber font-mono font-bold text-sm whitespace-nowrap">{model.price}</span>
        </div>

        {/* Description */}
        <p className="text-zinc-400 text-xs leading-relaxed mb-4">{model.desc}</p>

        {/* Stats row */}
        <div className="border border-border p-3 mb-4">
          <div className="grid grid-cols-3 gap-2">
            {model.stats.map((s) => (
              <div key={s.label}>
                <div className="text-zinc-500 text-[9px] font-mono uppercase tracking-widest mb-1">
                  {s.label}
                </div>
                <div
                  className={`text-xs font-bold font-mono ${
                    s.color === 'orange' ? 'text-orange-label' : 'text-white'
                  }`}
                >
                  {s.value}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom row: filename + ASK AI */}
        <div className="flex items-center justify-between mt-auto">
          <span className="text-zinc-500 text-[10px] font-mono">{model.file}</span>
          <button className="btn-amber text-[10px] px-4 py-2">ASK AI</button>
        </div>
      </div>
    </div>
  );
}
