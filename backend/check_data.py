"""Export full brochure text grouped by vehicle and section as JSON for frontend"""
import json

with open('data/vector_cache.json') as f:
    data = json.load(f)

# Group chunks by vehicle → section
by_vehicle = {}
for chunk in data['chunks']:
    meta = chunk.get('metadata', {})
    brand = meta.get('brand', '')
    model = meta.get('model', '')
    key = f"{brand} {model}".strip()
    if not key:
        continue
    section = meta.get('section', 'General')
    page = meta.get('page', 0)
    content = chunk.get('content', '')
    # Strip prefix header line
    lines = content.strip().split('\n')
    # Remove "Vehicle: X\nDocument: ... | Page: X | Section: Y\n\n" header
    clean_lines = []
    skip = 0
    for line in lines:
        if skip < 2 and (line.startswith('Vehicle:') or line.startswith('Document:')):
            skip += 1
            continue
        clean_lines.append(line)
    clean_text = '\n'.join(clean_lines).strip()
    if not clean_text:
        continue

    if key not in by_vehicle:
        by_vehicle[key] = []
    by_vehicle[key].append({
        'section': section,
        'page': page,
        'text': clean_text
    })

# Sort each vehicle's chunks by page
for key in by_vehicle:
    by_vehicle[key].sort(key=lambda x: (x['page'], x['section']))

# Print summary for each vehicle
for veh, chunks in by_vehicle.items():
    print(f"\n{'='*50}")
    print(f"VEHICLE: {veh} ({len(chunks)} chunks)")
    for c in chunks:
        print(f"  [p{c['page']:02d} {c['section']}] {c['text'][:120]}")
