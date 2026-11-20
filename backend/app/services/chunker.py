import re
from typing import List, Dict, Any

class DocumentChunker:
    """
    Splits brochure text into retrieval-optimized chunks with rich page and automotive metadata.
    """
    
    def __init__(self, target_chunk_size: int = 1000, chunk_overlap: int = 150):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, extracted_data: Dict[str, Any], document_id: str, vehicle_id: str = None) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        brand = extracted_data.get("brand", "")
        model = extracted_data.get("model", "")
        filename = extracted_data.get("filename", "")
        pages = extracted_data.get("pages", [])

        chunk_counter = 0

        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"]
            
            # Identify section hints
            section_hint = self._detect_section(page_text)
            
            # Split page text into manageable chunks
            text_slices = self._split_text(page_text)
            
            for slice_text in text_slices:
                if len(slice_text.strip()) < 50:
                    continue  # Ignore negligible snippets
                
                # Context prefix so vector embeddings are strongly anchored to the car model and page
                contextualized_content = (
                    f"Vehicle: {brand} {model}\n"
                    f"Document: {filename} | Page: {page_num} | Section: {section_hint}\n\n"
                    f"{slice_text.strip()}"
                )

                chunk_obj = {
                    "document_id": document_id,
                    "vehicle_id": vehicle_id,
                    "chunk_index": chunk_counter,
                    "content": contextualized_content,
                    "metadata": {
                        "filename": filename,
                        "brand": brand,
                        "model": model,
                        "page": page_num,
                        "section": section_hint,
                        "excerpt": slice_text.strip()[:180] + ("..." if len(slice_text.strip()) > 180 else "")
                    }
                }
                chunks.append(chunk_obj)
                chunk_counter += 1

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """Splits long text by paragraphs with overlap."""
        paragraphs = re.split(r'\n{2,}', text)
        slices: List[str] = []
        current_chunk = ""

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
                
            if len(current_chunk) + len(p) + 2 <= self.target_chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + p
            else:
                if current_chunk:
                    slices.append(current_chunk)
                    # Keep overlap
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                    current_chunk = overlap_text + "\n\n" + p
                else:
                    # Single paragraph exceeds chunk size, split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', p)
                    for s in sentences:
                        if len(current_chunk) + len(s) + 1 <= self.target_chunk_size:
                            current_chunk += (" " if current_chunk else "") + s
                        else:
                            if current_chunk:
                                slices.append(current_chunk)
                            current_chunk = s

        if current_chunk:
            slices.append(current_chunk)

        return slices

    def _detect_section(self, text: str) -> str:
        text_lower = text.lower()
        if any(k in text_lower for k in ["dimension", "length", "width", "height", "wheelbase", "boot space"]):
            return "Dimensions & Capacities"
        elif any(k in text_lower for k in ["engine", "transmission", "torque", "displacement", "powertrain", "gearbox"]):
            return "Engine & Powertrain"
        elif any(k in text_lower for k in ["safety", "airbag", "abs", "esc", "adas", "camera", "isofix"]):
            return "Safety & Security"
        elif any(k in text_lower for k in ["infotainment", "touchscreen", "audio", "bose", "apple carplay", "android auto"]):
            return "Infotainment & Technology"
        elif any(k in text_lower for k in ["interior", "sunroof", "ventilated", "leatherette", "climate control", "seats"]):
            return "Interior & Comfort"
        elif any(k in text_lower for k in ["exterior", "led", "headlamp", "alloys", "grille", "skid plate"]):
            return "Exterior Styling"
        elif any(k in text_lower for k in ["variant", "trim", "feature list", "standard features", "specifications"]):
            return "Variant Features & Specs"
        return "General Overview"

chunker = DocumentChunker()
