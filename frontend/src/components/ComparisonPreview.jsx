// RAG Citations section
export default function ComparisonPreview() {
  return (
    <section className="px-4 sm:px-6 pb-16 max-w-7xl mx-auto">
      {/* Label */}
      <div className="section-label mb-2" style={{ color: '#f97316' }}>VERIFIED RAG ANSWERS</div>

      {/* Heading */}
      <h2 className="text-3xl sm:text-4xl font-black text-white uppercase leading-none mb-4">
        ZERO HALLUCINATIONS.<br />
        PAGE-LEVEL CITATIONS.
      </h2>

      <p className="text-zinc-400 text-sm mb-6 max-w-lg">
        Every comparison between models or variants queries Supabase pgvector
        embeddings and links directly to the exact PDF brochure page.
      </p>

      {/* Citation pills */}
      <div className="flex flex-wrap gap-2 mb-8">
        <CitationPill file="Alcazar_2024.pdf" page="p.14" />
        <CitationPill file="Creta_Spec.pdf" page="p.09" />
      </div>

      {/* Sample query card */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-zinc-500 text-[10px] font-mono uppercase tracking-widest">
            SAMPLE QUERY: "ALCAZAR SIGNATURE VS CRETA SX(O)"
          </span>
          <span className="rag-badge text-[10px] px-2 py-1 bg-green-rag/10 border border-green-rag/30">
            2 SOURCES CITED
          </span>
        </div>
        <p className="text-zinc-300 text-sm leading-relaxed">
          Both share the 1.5L Turbo GDi engine (160 PS / 253 Nm) and Level 2 ADAS.
          Choose <span className="text-amber font-semibold">Alcazar</span> for 6/7-seat
          versatility, ventilated 2nd-row captain seats, and 579 L folded boot;
          choose Creta for compact city agility…
        </p>
      </div>
    </section>
  );
}

function CitationPill({ file, page }) {
  return (
    <span className="inline-flex items-center gap-2 bg-surface border border-border px-3 py-1.5 text-xs font-mono">
      <span className="text-amber">{file}</span>
      <span className="text-zinc-500">·</span>
      <span className="text-amber">{page}</span>
    </span>
  );
}
