import { useEffect, useState } from 'react';
import { BROCHURE_DATA } from '../data/modelsData';
import VehicleDetail from './VehicleDetail';
import Footer from '../components/Footer';

const descriptions = {
  alcazar: 'Designed for families that expect more, Alcazar combines generous three-row space with confident design and premium technology.',
  creta: 'A defining SUV with a bold presence, refined comfort and a complete range of petrol and diesel powertrains.',
  seltos: 'A muscular, technology-rich SUV that blends striking road presence with advanced safety and everyday versatility.',
  nexon: 'Compact in proportion and strong in character, Nexon brings expressive design, exceptional safety and multiple powertrain choices.',
};

export default function VehicleCatalogPage({ onOpenChat }) {
  const [activeFilter, setActiveFilter] = useState('All');
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [first, setFirst] = useState(BROCHURE_DATA[0].id);
  const [second, setSecond] = useState(BROCHURE_DATA[1].id);

  useEffect(() => {
    const showVehicleFromHash = () => {
      const match = window.location.hash.match(/^#vehicle\/([^/?#]+)/);
      if (match) {
        const vehicle = BROCHURE_DATA.find((item) => item.id === match[1]);
        if (vehicle) setSelectedVehicle(vehicle);
      } else {
        setSelectedVehicle(null);
      }
    };
    showVehicleFromHash();
    window.addEventListener('hashchange', showVehicleFromHash);
    return () => window.removeEventListener('hashchange', showVehicleFromHash);
  }, []);

  const openVehicle = (vehicle) => {
    setSelectedVehicle(vehicle);
    window.history.replaceState(null, '', `#vehicle/${vehicle.id}`);
  };

  const closeVehicle = () => {
    setSelectedVehicle(null);
    window.history.replaceState(null, '', '#models');
  };

  if (selectedVehicle) {
    return (
      <>
        <VehicleDetail vehicle={selectedVehicle} onBack={closeVehicle} onOpenChat={onOpenChat} />
        <Footer />
      </>
    );
  }

  const brands = ['All', ...new Set(BROCHURE_DATA.map((vehicle) => vehicle.brand))];
  const filtered = activeFilter === 'All'
    ? BROCHURE_DATA
    : BROCHURE_DATA.filter((vehicle) => vehicle.brand === activeFilter);
  const left = BROCHURE_DATA.find((vehicle) => vehicle.id === first);
  const right = BROCHURE_DATA.find((vehicle) => vehicle.id === second);

  return (
    <main>
      <section className="hero-section relative min-h-[760px] flex items-end overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1619767886558-efdc259cde1a?auto=format&fit=crop&w=2400&q=90"
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 hero-overlay" />
        <div className="relative z-10 max-w-[1500px] mx-auto w-full px-5 sm:px-8 lg:px-12 pb-16 sm:pb-20">
          <p className="text-xs sm:text-sm font-semibold uppercase tracking-[0.32em] mb-5 text-white/75">Discover the extraordinary</p>
          <h1 className="text-5xl sm:text-7xl lg:text-[96px] leading-[0.88] font-black tracking-[-0.055em] max-w-5xl">
            FIND YOUR<br />NEXT DRIVE.
          </h1>
          <p className="mt-7 text-base sm:text-lg text-white/75 max-w-xl leading-8">
            Explore distinctive SUVs, detailed configurations and the features that make every journey feel exceptional.
          </p>
          <a href="#models" className="mt-8 inline-flex items-center gap-5 border-b border-white pb-3 text-xs font-bold uppercase tracking-[0.22em]">
            Explore models <span className="text-xl">↓</span>
          </a>
        </div>
      </section>

      <section id="models" className="bg-[#f2f0ea] text-[#171719] py-20 sm:py-28">
        <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12">
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8 mb-12">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#77766f] mb-4">The collection</p>
              <h2 className="text-4xl sm:text-6xl font-black tracking-[-0.04em]">CHOOSE YOUR MODEL</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {brands.map((brand) => (
                <button
                  key={brand}
                  onClick={() => setActiveFilter(brand)}
                  className={`px-5 py-3 border text-xs font-bold uppercase tracking-[0.14em] transition-colors ${
                    activeFilter === brand
                      ? 'bg-[#171719] text-white border-[#171719]'
                      : 'border-[#bdbbb3] hover:border-[#171719]'
                  }`}
                >
                  {brand}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-5 gap-y-14">
            {filtered.map((vehicle) => (
              <article key={vehicle.id} className="group cursor-pointer" onClick={() => openVehicle(vehicle)}>
                <div className="relative h-[360px] sm:h-[480px] overflow-hidden bg-[#dedbd2]">
                  <img
                    src={vehicle.image}
                    alt={vehicle.fullName}
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.035]"
                  />
                  <div className="absolute inset-x-0 bottom-0 h-36 model-card-gradient" />
                  <div className="absolute left-5 bottom-5 text-white">
                    <p className="text-xs uppercase tracking-[0.2em] mb-2">{vehicle.brand}</p>
                    <p className="text-3xl sm:text-4xl font-black">{vehicle.model}</p>
                  </div>
                </div>
                <div className="pt-6">
                  <p className="text-sm sm:text-base leading-7 text-[#65645e] max-w-xl min-h-[56px]">
                    {descriptions[vehicle.id]}
                  </p>
                  <div className="mt-6 flex items-center justify-between border-t border-[#bdbbb3] pt-5">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.18em] text-[#85847d] mb-1">Starting from</p>
                      <p className="text-lg font-bold">{vehicle.priceRange.split(' – ')[0]}</p>
                    </div>
                    <button className="text-xs font-bold uppercase tracking-[0.16em] border-b border-[#171719] pb-2">
                      Discover model →
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="compare" className="bg-[#171719] text-white py-20 sm:py-28">
        <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-white/50 mb-4">Side by side</p>
          <h2 className="text-4xl sm:text-6xl font-black tracking-[-0.04em] mb-12">COMPARE MODELS</h2>
          <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr] gap-4 mb-8">
            {[{ value: first, set: setFirst }, { value: second, set: setSecond }].map((select, index) => (
              <select
                key={index}
                value={select.value}
                onChange={(event) => select.set(event.target.value)}
                className="w-full bg-transparent border border-white/25 px-5 py-5 text-sm font-semibold"
              >
                {BROCHURE_DATA.map((vehicle) => (
                  <option key={vehicle.id} value={vehicle.id} className="text-black">
                    {vehicle.fullName}
                  </option>
                ))}
              </select>
            ))}
          </div>
          {left && right && (
            <ComparisonTable left={left} right={right} />
          )}
        </div>
      </section>

          <section id="safety" className="bg-[#e3e1dc] py-20 sm:py-24 text-[#171719]">
            <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12">
              <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#77766f] mb-4">Confidence comes standard</p>
              <h2 className="text-4xl sm:text-6xl font-black tracking-[-0.04em] mb-12">SAFETY, ENGINEERED INTO EVERY JOURNEY.</h2>
              <div className="grid md:grid-cols-3 border-t border-[#aaa79e]">
                {[
                  ['Intelligent assistance', 'Lane guidance, collision avoidance and adaptive cruise control support attentive driving.'],
                  ['Advanced protection', 'Multiple airbags, stability control and reinforced body structures protect occupants.'],
                  ['Complete awareness', 'Parking cameras and sensors provide clear visibility around the vehicle.'],
                ].map(([title, text], index) => (
                  <div key={title} className="py-8 md:pr-8 md:border-r border-b md:border-b-0 border-[#aaa79e] last:border-r-0">
                    <p className="text-xs text-[#85847d] mb-8">0{index + 1}</p>
                    <h3 className="text-xl sm:text-2xl font-bold mb-4">{title}</h3>
                    <p className="text-base leading-7 text-[#626159]">{text}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section id="ownership" className="bg-[#b4a58d] py-20 sm:py-24 text-[#171719]">
        <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12 flex flex-col lg:flex-row items-start lg:items-end justify-between gap-8">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.24em] mb-5">Ownership guidance</p>
            <h2 className="text-4xl sm:text-6xl font-black tracking-[-0.04em] max-w-3xl">FIND THE RIGHT MODEL FOR YOU.</h2>
          </div>
          <button onClick={onOpenChat} className="bg-[#171719] text-white px-8 py-5 text-xs font-bold uppercase tracking-[0.18em]">
            Open GearGuide
          </button>
        </div>
      </section>
      <Footer />
    </main>
  );
}

function ComparisonTable({ left, right }) {
  const rows = [
    ['Starting price', left.priceRange, right.priceRange],
    ['Seating', left.specs.seating, right.specs.seating],
    ['Length', left.specs.dimensions.length, right.specs.dimensions.length],
    ['Wheelbase', left.specs.dimensions.wheelbase, right.specs.dimensions.wheelbase],
    ['Boot space', left.specs.dimensions.bootSpace, right.specs.dimensions.bootSpace],
    ['Ground clearance', left.specs.dimensions.groundClearance, right.specs.dimensions.groundClearance],
  ];
  return (
    <div className="border-t border-white/20">
      {rows.map((row) => (
        <div key={row[0]} className="grid grid-cols-[120px_1fr_1fr] sm:grid-cols-[180px_1fr_1fr] border-b border-white/20 py-5 sm:py-7">
          <div className="text-white/50 text-xs sm:text-sm">{row[0]}</div>
          <div className="pr-3 text-sm sm:text-lg font-semibold">{row[1]}</div>
          <div className="pl-3 border-l border-white/20 text-sm sm:text-lg font-semibold">{row[2]}</div>
        </div>
      ))}
      <div className="grid grid-cols-2 gap-4 pt-6">
        <div className="text-sm sm:text-xl">{left.fullName}</div>
        <div className="text-sm sm:text-xl">{right.fullName}</div>
      </div>
    </div>
  );
}
