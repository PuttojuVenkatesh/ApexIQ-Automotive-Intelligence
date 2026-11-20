import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class PDFExtractor:
    """
    Extracts text, structural sections, and vehicle metadata from automotive brochures.
    Supports PyMuPDF (fitz) and pypdf.
    """
    
    KNOWN_MODELS = [
        {"brand": "Hyundai", "model": "Creta", "aliases": ["creta", "creta n line"]},
        {"brand": "Hyundai", "model": "Alcazar", "aliases": ["alcazar"]},
        {"brand": "Kia", "model": "Seltos", "aliases": ["seltos"]},
        {"brand": "Tata", "model": "Nexon", "aliases": ["nexon", "nexon ev"]},
        {"brand": "Mahindra", "model": "Thar", "aliases": ["thar", "thar roxx"]},
        {"brand": "Mahindra", "model": "Scorpio-N", "aliases": ["scorpio", "scorpio-n"]},
        {"brand": "Maruti Suzuki", "model": "Grand Vitara", "aliases": ["grand vitara", "brezza"]}
    ]

    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Brochure PDF not found at {file_path}")

        pages_data: List[Dict[str, Any]] = []
        total_text = ""
        
        # Try PyMuPDF (fitz) first
        try:
            import fitz
            doc = fitz.open(str(path))
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                text = page.get_text("text")
                clean_text = self._clean_text(text)
                if clean_text:
                    pages_data.append({
                        "page_number": page_idx + 1,
                        "text": clean_text
                    })
                    total_text += f"\n--- Page {page_idx + 1} ---\n" + clean_text
            doc.close()
        except ImportError:
            # Fallback to pypdf
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                clean_text = self._clean_text(text)
                if clean_text:
                    pages_data.append({
                        "page_number": page_idx + 1,
                        "text": clean_text
                    })
                    total_text += f"\n--- Page {page_idx + 1} ---\n" + clean_text

        # Detect vehicle brand and model
        brand, model = self._detect_vehicle(path.name, total_text)
        
        # Extract structured specifications
        specs = self._extract_specs(total_text)
        
        return {
            "filename": path.name,
            "page_count": len(pages_data),
            "brand": brand,
            "model": model,
            "pages": pages_data,
            "full_text": total_text,
            "specs": specs
        }

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove repeated non-standard characters and normalize whitespace
        text = re.sub(r'[\r\t]', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()

    def _detect_vehicle(self, filename: str, full_text: str) -> (str, str):
        target = (filename + " " + full_text[:2000]).lower()
        for item in self.KNOWN_MODELS:
            for alias in item["aliases"]:
                if alias in target:
                    return item["brand"], item["model"]
        
        # General heuristic
        for brand in ["Hyundai", "Kia", "Tata", "Mahindra", "Maruti Suzuki", "Honda", "Toyota"]:
            if brand.lower() in target:
                return brand, "Vehicle"
                
        return "Automotive", "Vehicle"

    def _extract_specs(self, text: str) -> Dict[str, Any]:
        """Heuristically extracts key specs from text (engines, dimensions, power)."""
        specs = {
            "engines": [],
            "transmissions": [],
            "dimensions": {},
            "safety_highlights": []
        }
        
        # Power & Torque patterns
        power_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:ps|bhp|kw|hp)', text, re.IGNORECASE)
        torque_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:nm|kgm)', text, re.IGNORECASE)
        if power_matches:
            specs["detected_power_outputs"] = list(set(power_matches[:4]))
        if torque_matches:
            specs["detected_torques"] = list(set(torque_matches[:4]))
            
        # Common transmission keywords
        for trans in ["Manual", "Automatic", "DCT", "IVT", "iMT", "AMT", "Torque Converter", "AT", "MT"]:
            if re.search(r'\b' + trans + r'\b', text, re.IGNORECASE):
                specs["transmissions"].append(trans)
        specs["transmissions"] = list(set(specs["transmissions"]))

        # Safety keywords
        safety_keys = [
            "6 Airbags", "Airbags", "ABS with EBD", "Electronic Stability Control (ESC)",
            "Hill-start Assist Control (HAC)", "ADAS", "Level 2 ADAS",
            "360 Degree Camera", "Blind Spot Monitor", "ISOFIX Child Seat"
        ]
        for key in safety_keys:
            if re.search(r'\b' + re.escape(key) + r'\b', text, re.IGNORECASE):
                specs["safety_highlights"].append(key)
                
        return specs

pdf_extractor = PDFExtractor()
