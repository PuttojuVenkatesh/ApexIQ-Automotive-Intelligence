export default function VehicleDetail({ vehicle: v, onBack, onOpenChat }) {
  return (
    <main className="bg-[#f2f0ea] text-[#171719]">
      <section className="relative h-[72vh] min-h-[620px] overflow-hidden bg-[#171719] text-white">
        <img src={v.image} alt={v.fullName} className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 detail-overlay" />
        <div className="relative z-10 max-w-[1500px] mx-auto h-full px-5 sm:px-8 lg:px-12 pt-24 flex flex-col justify-end pb-14 sm:pb-18">
          <button onClick={onBack} className="absolute top-28 left-5 sm:left-8 lg:left-12 text-xs font-bold uppercase tracking-[0.18em] text-white/80 hover:text-white">
            ← All models
          </button>
          <p className="text-xs font-bold uppercase tracking-[0.28em] mb-5">{v.brand}</p>
          <h1 className="text-5xl sm:text-7xl lg:text-[92px] leading-none font-black tracking-[-0.05em]">{v.fullName}</h1>
          <p className="mt-5 text-xl sm:text-2xl text-white/75">{v.tagline}</p>
        </div>
      </section>

      <section className="py-16 sm:py-24">
        <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12 grid lg:grid-cols-[1fr_2fr] gap-10 lg:gap-20">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#77766f]">At a glance</p>
          <div>
            <h2 className="text-4xl sm:text-6xl font-black tracking-[-0.04em] leading-[1.02] mb-8">
              {v.highlights[0]}
            </h2>
            <p className="text-lg sm:text-xl leading-9 text-[#5e5d57] max-w-3xl">
              {v.fullName} brings together expressive styling, a carefully considered cabin and a broad range of technology.
              Every configuration is designed around comfort, control and confidence on the road.
            </p>
            <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 border-t border-[#bbb8ae]">
              {[
                ['Price', v.priceRange],
                ['Seating', v.specs.seating],
                ['Length', v.specs.dimensions.length],
                ['Wheelbase', v.specs.dimensions.wheelbase],
              ].map(([label, value]) => (
                <div key={label} className="py-6 pr-4 border-b border-[#bbb8ae]">
                  <p className="text-[10px] uppercase tracking-[0.18em] text-[#85847d] mb-2">{label}</p>
                  <p className="text-sm sm:text-base font-bold">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-[#171719] text-white py-16 sm:py-24">
        <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-white/50 mb-4">Performance</p>
          <h2 className="text-4xl sm:text-6xl font-black tracking-[-0.04em] mb-12">POWERTRAIN</h2>
          <div className="grid md:grid-cols-3 border-t border-white/20">
            {v.specs.engine.map((engine) => (
              <div key={engine.label} className="py-8 md:pr-8 md:border-r border-b md:border-b-0 border-white/20 last:border-r-0">
                <p className="text-xs uppercase tracking-[0.18em] text-white/50 mb-5">{engine.label}</p>
                <p className="text-xl sm:text-2xl font-bold">{engine.value}</p>
              </div>
            ))}
          </div>
          <div className="mt-10 flex flex-wrap gap-3">
            {v.specs.transmission.map((item) => (
              <span key={item} className="border border-white/25 px-4 py-3 text-sm">{item}</span>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 sm:py-24">
        <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#77766f] mb-4">Key strengths</p>
          <h2 className="text-4xl sm:text-6xl font-black tracking-[-0.04em] mb-12">DISTINCTIVE FEATURES</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 border-t border-[#bbb8ae]">
            {v.highlights.map((highlight, index) => (
              <div key={highlight} className="border-b border-r border-[#bbb8ae] py-7 pr-7 min-h-[150px]">
                <p className="text-xs text-[#99978e] mb-5">0{index + 1}</p>
                <p className="text-lg sm:text-xl font-bold leading-8">{highlight}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-[#ddd9ce] py-16 sm:py-24">
        <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12 grid md:grid-cols-2 gap-16 lg:gap-24">
          <DetailList title="Technology & comfort" items={v.specs.technology} />
          <DetailList title="Safety" items={v.specs.safety} />
          <DetailList title="Exterior design" items={v.specs.exterior} />
          <DetailList title="Driver assistance" items={v.specs.adas.features} />
        </div>
      </section>

      <section className="py-16 sm:py-24">
        <div className="max-w-[1500px] mx-auto px-5 sm:px-8 lg:px-12">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-[#77766f] mb-4">Choose your configuration</p>
          <h2 className="text-4xl sm:text-6xl font-black tracking-[-0.04em] mb-12">VARIANTS</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 border-t border-[#bbb8ae]">
            {v.variants.map((variant) => (
              <div key={variant.name} className="border-b border-r border-[#bbb8ae] py-6 pr-6">
                <p className="text-lg font-bold mb-4">{variant.name}</p>
                <div className="flex flex-wrap gap-2">
                  {variant.fuel.map((fuel) => (
                    <span key={fuel} className="text-xs text-[#68675f]">{fuel}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-14 grid sm:grid-cols-2 gap-8">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-[#85847d] mb-4">Available colours</p>
              <p className="text-base leading-8">{v.colors.join('  ·  ')}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-[#85847d] mb-4">Warranty</p>
              <p className="text-base leading-8">{v.specs.warranty}</p>
            </div>
          </div>

          <div className="mt-16 flex flex-col sm:flex-row gap-4">
            <button onClick={onOpenChat} className="bg-[#171719] text-white px-8 py-5 text-xs font-bold uppercase tracking-[0.18em]">
              Ask about this model
            </button>
            <button onClick={onBack} className="border border-[#171719] px-8 py-5 text-xs font-bold uppercase tracking-[0.18em]">
              View all models
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}

function DetailList({ title, items }) {
  return (
    <div>
      <h3 className="text-xs font-bold uppercase tracking-[0.24em] mb-6">{title}</h3>
      <div className="space-y-4">
        {items.map((item) => (
          <p key={item} className="text-base sm:text-lg border-b border-[#aaa79c] pb-4">{item}</p>
        ))}
      </div>
    </div>
  );
}
