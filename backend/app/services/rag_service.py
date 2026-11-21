import re
from typing import Dict, List, Any, Optional
from app.core.config import settings
from app.db.supabase_client import db
from app.services.embeddings import embedding_service

class RAGService:
    def __init__(self):
        self.top_k = settings.TOP_K_CHUNKS
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self._answer_cache = {}

    def invalidate_cache(self):
        self._answer_cache.clear()

    def query(
        self,
        user_query: str,
        session_id: Optional[str] = None,
        filter_vehicle_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end RAG:
        1. Embed user query
        2. Retrieve most relevant brochure chunks via pgvector / cosine search
        3. Assemble context with page and document citations
        4. Build a verified answer from retrieved brochure passages
        5. Persist to chat history and return answer + sources
        """
        conversation_context = self._conversation_context(user_query, conversation_history or [])
        retrieval_query = f"{conversation_context} {user_query}".strip()
        cache_key = f"{retrieval_query.lower()}|{filter_vehicle_id or ''}"
        cached = self._answer_cache.get(cache_key)
        if cached:
            if not session_id:
                session_id = db.create_chat_session(title=user_query[:40] + ("..." if len(user_query) > 40 else ""))
            return {
                "session_id": session_id,
                "query": user_query,
                "answer": cached["answer"],
                "sources": cached["sources"],
                "related_vehicles": cached["related_vehicles"],
                "chunks_retrieved": cached["chunks_retrieved"]
            }

        if not session_id:
            session_id = db.create_chat_session(title=user_query[:40] + ("..." if len(user_query) > 40 else ""))

        # 1. Embed query
        query_vector = embedding_service.get_embedding(retrieval_query)

        # 2. Vector retrieval
        candidate_count = max(self.top_k, min(len(db.local_chunks) or 100, 500))
        retrieval_candidates = db.match_document_chunks(
            query_embedding=query_vector,
            match_threshold=0.05,
            match_count=candidate_count,
            filter_vehicle_id=filter_vehicle_id
        )
        ranked_chunks = self._rerank_chunks(retrieval_query, retrieval_candidates)
        requested_models = self._models_in_question(
            retrieval_query,
            db.local_chunks + ranked_chunks,
        )
        comparison_intent = bool(re.search(
            r"\b(compare|comparison|versus|vs|which one|better|best|recommend|differences?)\b",
            retrieval_query.lower(),
        ))
        if comparison_intent and len(requested_models) >= 2:
            total_comparison_chunks = min(24, max(self.top_k, 6 * len(requested_models)))
            per_model_limit = max(1, total_comparison_chunks // len(requested_models))
            matched_chunks = self._balance_comparison_chunks(
                ranked_chunks,
                requested_models,
                per_model_limit,
            )
        else:
            matched_chunks = ranked_chunks[:self.top_k]

        # 3. Format sources and context
        sources = []
        context_blocks = []
        seen_pages = set()

        for c in matched_chunks:
            meta = c.get("metadata", {})
            doc_name = meta.get("filename", "Brochure")
            page = meta.get("page", 1)
            section = meta.get("section", "General")
            
            # Avoid duplicate citations for identical page in source badge list
            citation_key = f"{doc_name}-p{page}"
            if citation_key not in seen_pages:
                sources.append({
                    "document": doc_name,
                    "brand": meta.get("brand", ""),
                    "model": meta.get("model", ""),
                    "page": page,
                    "section": section,
                    "excerpt": meta.get("excerpt", c.get("content", "")[:150]),
                    "similarity": round(float(c.get("similarity", 0.0)), 3)
                })
                seen_pages.add(citation_key)
                
            context_blocks.append(
                f"[Source: {doc_name} | Page {page} | {section}]\n{c.get('content', '')}"
            )

        context_text = "\n\n---\n\n".join(context_blocks)

        # 4. Generate an answer only from the retrieved brochure passages.
        answer = self._generate_brochure_answer(
            user_query,
            context_text,
            sources,
            conversation_context,
            matched_chunks,
        )
        related_vehicles = self._related_vehicles(sources)
        retrieved_models = {
            str(chunk.get("metadata", {}).get("model", "")).lower()
            for chunk in matched_chunks
            if chunk.get("metadata", {}).get("model")
        }
        named_models = {
            model for model in retrieved_models
            if re.search(rf"\b{re.escape(model)}\b", user_query.lower())
        }
        if (
            not conversation_context
            and len(named_models) < 2
            and re.search(r"\b(which one|better|best|recommend)\b", user_query.lower())
        ):
            related_vehicles = []

        # 5. Persist to history
        db.add_chat_message(session_id=session_id, role="user", content=user_query)
        db.add_chat_message(session_id=session_id, role="assistant", content=answer, sources=sources)

        result = {
            "session_id": session_id,
            "query": user_query,
            "answer": answer,
            "sources": sources,
            "related_vehicles": related_vehicles,
            "chunks_retrieved": len(matched_chunks)
        }
        self._answer_cache[cache_key] = {
            "answer": answer,
            "sources": sources,
            "related_vehicles": related_vehicles,
            "chunks_retrieved": len(matched_chunks)
        }
        return result

    @staticmethod
    def _related_vehicles(sources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        vehicle_ids = {
            "alcazar": "alcazar",
            "creta": "creta",
            "seltos": "seltos",
            "nexon": "nexon",
        }
        related = []
        seen = set()
        for source in sources:
            model = str(source.get("model", "")).strip()
            vehicle_id = vehicle_ids.get(model.lower())
            if vehicle_id and vehicle_id not in seen:
                related.append({
                    "label": f"Explore {source.get('brand', '').strip()} {model}".strip(),
                    "url": f"#vehicle/{vehicle_id}",
                })
                seen.add(vehicle_id)
        return related

    @staticmethod
    def _all_models_requested(query: str) -> bool:
        return bool(re.search(
            r"\b(?:all|every|each)\b.{0,40}\b(?:brochures?|vehicles?|models?|cars?)\b",
            query.lower(),
        ))

    @staticmethod
    def _models_in_question(query: str, chunks: List[Dict[str, Any]]) -> List[str]:
        available_models = list(dict.fromkeys(
            str(chunk.get("metadata", {}).get("model", "")).strip()
            for chunk in chunks
            if chunk.get("metadata", {}).get("model")
        ))
        if RAGService._all_models_requested(query):
            return available_models

        mentioned = [
            model for model in available_models
            if re.search(rf"\b{re.escape(model)}\b", query, re.IGNORECASE)
        ]
        return sorted(mentioned, key=lambda model: query.lower().find(model.lower()))

    @staticmethod
    def _balance_comparison_chunks(
        chunks: List[Dict[str, Any]],
        models: List[str],
        per_model_limit: int,
    ) -> List[Dict[str, Any]]:
        model_chunks: Dict[str, List[Dict[str, Any]]] = {
            model.lower(): [] for model in models
        }
        for chunk in chunks:
            model = str(chunk.get("metadata", {}).get("model", "")).strip().lower()
            if model in model_chunks:
                model_chunks[model].append(chunk)

        balanced = []
        for index in range(per_model_limit):
            for model in model_chunks:
                if index < len(model_chunks[model]):
                    balanced.append(model_chunks[model][index])
        return balanced

    @staticmethod
    def _conversation_context(query: str, history: List[Dict[str, str]]) -> str:
        model_names = {
            str(chunk.get("metadata", {}).get("model", "")).strip().lower()
            for chunk in db.local_chunks
            if chunk.get("metadata", {}).get("model")
        }
        query_models = {
            model for model in model_names
            if re.search(rf"\b{re.escape(model)}\b", query.lower())
        }
        if query_models or not history or not re.search(
            r"\b(it|that|them|those|which one|what about|how about|better|best|compare them|and the)\b",
            query.lower(),
        ):
            return ""
        for message in reversed(history[-8:]):
            if message.get("role") != "user" or not message.get("content"):
                continue
            prior_query = str(message["content"]).strip()
            prior_models = {
                model for model in model_names
                if re.search(rf"\b{re.escape(model)}\b", prior_query.lower())
            }
            if len(prior_models) >= 2:
                return prior_query
        return ""

    @staticmethod
    def _rerank_chunks(query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        stop_words = {
            "a", "an", "and", "are", "about", "does", "for", "from", "how", "i",
            "is", "it", "me", "of", "on", "or", "the", "their", "this", "to",
            "vs", "what", "which", "with", "you",
        }
        query_terms = {
            term for term in re.findall(r"[a-z0-9]+", query.lower())
            if len(term) > 2 and term not in stop_words
        }
        query_lower = query.lower()
        if any(term in query_lower for term in ["engine", "power", "torque", "performance"]):
            query_terms.update({"engine", "power", "torque", "displacement", "configuration", "transmission"})
        if any(term in query_lower for term in ["space", "room", "boot", "luggage", "cargo"]):
            query_terms.update({"dimensions", "wheelbase", "boot", "space", "seating", "capacity", "luggage"})
        if any(term in query_lower for term in ["safety", "airbag", "adas", "assist"]):
            query_terms.update({"safety", "airbag", "adas", "brake", "stability", "collision"})
        if re.search(r"\b(features?|equipment|specifications?)\b", query_lower):
            query_terms.update({
                "engine", "power", "torque", "transmission", "fuel", "mileage",
                "safety", "airbag", "adas", "abs", "esc", "sunroof", "ventilated",
                "seat", "touchscreen", "infotainment", "audio", "connected",
                "camera", "cruise", "climate", "alloy", "led", "boot",
            })
        if re.search(r"\b(compare|vs|versus)\b", query_lower):
            query_terms.update({
                "dimensions", "length", "width", "wheelbase", "boot", "seating",
                "capacity", "engine", "power", "torque", "transmission", "fuel",
            })
        available_models = {
            str(chunk.get("metadata", {}).get("model", "")).lower()
            for chunk in db.local_chunks + chunks
            if chunk.get("metadata", {}).get("model")
        }
        requested_models = {
            model for model in available_models
            if re.search(rf"\b{re.escape(model)}\b", query_lower)
        }
        if requested_models:
            chunks = [
                chunk for chunk in chunks
                if str(chunk.get("metadata", {}).get("model", "")).lower() in requested_models
            ]
        high_value_terms = {
            "engine", "power", "torque", "transmission", "diesel", "petrol",
            "safety", "airbag", "adas", "dimensions", "wheelbase", "boot",
            "seating", "sunroof", "mileage", "fuel", "variant", "length",
            "width", "capacity",
        }

        def score(chunk: Dict[str, Any]) -> float:
            metadata = chunk.get("metadata", {})
            text = f"{metadata.get('section', '')} {chunk.get('content', '')}".lower()
            tokens = set(re.findall(r"[a-z0-9]+", text))
            overlap = sum(
                2.0 if term in high_value_terms else 0.5 if term in {"hyundai", "kia", "tata"} else 1.0
                for term in query_terms
                if term in tokens
            )
            model = str(metadata.get("model", "")).lower()
            if model and model in query.lower():
                overlap += 1.5
            if re.search(r"\b(compare|vs|versus)\b", query_lower) and "dimension" in str(metadata.get("section", "")).lower():
                overlap += 2.0
            return overlap + float(chunk.get("similarity", 0.0)) * 0.05

        return sorted(chunks, key=score, reverse=True)

    def _generate_brochure_answer(
        self,
        query: str,
        context: str,
        sources: List[Dict[str, Any]],
        conversation_context: str = "",
        matched_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        return self._synthesize_from_brochures(
            query,
            context,
            sources,
            conversation_context,
            matched_chunks or [],
        )

    def _synthesize_from_brochures(
        self,
        query: str,
        context: str,
        sources: List[Dict[str, Any]],
        conversation_context: str = "",
        matched_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Build a concise conversational response only from retrieved brochure passages.
        """
        if not context or not sources:
            return (
                "I searched through the official vehicle brochures in the knowledge base, "
                "but I couldn't locate specific specifications matching your query. "
                "Could you please clarify the vehicle model (e.g., Hyundai Creta, Hyundai Alcazar, Kia Seltos, or Tata Nexon) "
                "or the specific feature you'd like to check?"
            )

        query_lower = query.lower()
        effective_question = f"{conversation_context} {query}".strip()
        effective_question_lower = effective_question.lower()
        cars_mentioned = list(dict.fromkeys(
            f"{s.get('brand', '')} {s.get('model', '')}".strip()
            for s in sources if s.get('brand')
        ))
        car_str = " and ".join(cars_mentioned) if cars_mentioned else "the vehicle"

        is_choice_question = any(term in query_lower for term in ["better", "best", "which one", "recommend"])
        is_comparison_query = bool(re.search(r"\b(compare|vs|versus)\b", query_lower))
        available_models = {
            str(chunk.get("metadata", {}).get("model", "")).strip().lower()
            for chunk in db.local_chunks + (matched_chunks or [])
            if chunk.get("metadata", {}).get("model")
        }
        named_models = {
            model for model in available_models
            if re.search(rf"\b{re.escape(model)}\b", effective_question_lower)
        }
        if self._all_models_requested(effective_question):
            named_models = available_models
        if len(named_models) >= 2 and is_choice_question:
            if len(named_models) == 2:
                recommendation = self._recommend_from_brochures(
                    effective_question,
                    matched_chunks or [],
                )
                if recommendation:
                    return recommendation
            comparison = self._compare_from_brochures(effective_question, matched_chunks or [])
            if comparison:
                return (
                    "The brochures don't establish one overall winner without a priority. "
                    "Here are the differences they document:\n\n"
                    f"{comparison}"
                )

        if len(named_models) >= 2 and is_comparison_query:
            comparison = self._compare_from_brochures(effective_question, matched_chunks or [])
            if comparison:
                return comparison

        if (is_choice_question or is_comparison_query) and len(named_models) < 2:
            return (
                "Which two models are you choosing between, and what matters most to you?"
            )

        # Categorize retrieved knowledge points
        specs_points = []
        safety_points = []
        tech_points = []
        comfort_points = []
        general_points = []

        for c in context.split("\n\n---\n\n"):
            # Clean content lines
            raw_lines = c.split("\n")
            cleaned_lines = []
            for l in raw_lines:
                l_str = l.strip()
                if not l_str or l_str.startswith("[Source:") or l_str.startswith("Vehicle:") or l_str.startswith("Document:"):
                    continue
                cleaned_lines.append(l_str)

            combined_snippet = self._concise_point("\n".join(cleaned_lines), query_lower)
            if not combined_snippet:
                continue

            snippet_lower = combined_snippet.lower()
            if any(k in snippet_lower for k in ["engine", "power", "torque", "transmission", "speed", "diesel", "petrol", "gdi", "crdi"]):
                specs_points.append(combined_snippet)
            elif any(k in snippet_lower for k in ["safety", "airbag", "abs", "esc", "adas", "stability", "hac", "isofix", "sensor"]):
                safety_points.append(combined_snippet)
            elif any(k in snippet_lower for k in ["touchscreen", "infotainment", "audio", "bose", "cluster", "screen", "connected"]):
                tech_points.append(combined_snippet)
            elif any(k in snippet_lower for k in ["seat", "sunroof", "ventilated", "leather", "interior", "recline", "space"]):
                comfort_points.append(combined_snippet)
            else:
                general_points.append(combined_snippet)

        # Assemble conversational response
        response = f"Verified information for **{car_str}**:\n\n"

        if "compare" in query_lower or " vs " in query_lower:
            response = (
                f"Here is a side-by-side comparison of **{car_str}**:\n\n"
            )

        if any(term in query_lower for term in ["engine", "power", "torque", "performance"]):
            engine_answer = self._engine_answer(context, car_str)
            if engine_answer:
                return engine_answer

        requested_sections = []
        if any(word in query_lower for word in ["engine", "power", "torque", "fuel", "transmission", "performance"]):
            requested_sections.append(("Powertrain", specs_points))
        if any(word in query_lower for word in ["safety", "airbag", "adas", "assist", "brake"]):
            requested_sections.append(("Safety & assistance", safety_points))
        if any(word in query_lower for word in ["seat", "comfort", "space", "sunroof", "interior"]):
            requested_sections.append(("Cabin & comfort", comfort_points))
        if any(word in query_lower for word in ["technology", "screen", "display", "audio", "infotainment", "feature"]):
            requested_sections.append(("Technology", tech_points))

        if not requested_sections:
            requested_sections = [
                ("Powertrain", specs_points),
                ("Safety & assistance", safety_points),
                ("Cabin & comfort", comfort_points),
                ("Technology", tech_points),
            ]
        if not any(points for _, points in requested_sections):
            requested_sections = [("Key details", general_points or specs_points or safety_points or tech_points)]

        for heading, points in requested_sections:
            unique_points = list(dict.fromkeys(points))[:3]
            if unique_points:
                response += f"### {heading}\n"
                for point in unique_points:
                    response += f"- {point}\n"
                response += "\n"

        return response.strip()

    @staticmethod
    def _concise_point(text: str, query: str = "", max_characters: int = 240) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if any(term in query for term in ["engine", "power", "torque", "performance"]):
            technical_rows = []
            keywords = ("displacement", "max. power", "max power", "torque", "transmission", "1.5l")
            for index, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in keywords):
                    technical_rows.append(line)
                    if index + 1 < len(lines):
                        technical_rows.append(lines[index + 1])
            if technical_rows:
                text = " ".join(dict.fromkeys(technical_rows))

        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        concise = " ".join(sentence.strip() for sentence in sentences[:2] if sentence.strip())
        if len(concise) > max_characters:
            concise = concise[:max_characters].rsplit(" ", 1)[0].rstrip(" ,;:-") + "…"
        return concise

    @staticmethod
    def _engine_answer(context: str, car_name: str) -> str:
        normalized = re.sub(r"\s+", " ", context)
        engine_pattern = re.compile(
            r"1\.5\s*l\s+(?:MPi|U2\s+CRDi|Turbo\s+GDi)\s+(?:petrol|diesel)",
            re.IGNORECASE,
        )
        engines = list(dict.fromkeys(match.group(0) for match in engine_pattern.finditer(normalized)))
        power_match = re.search(
            r"Max\.\s*power\s+([\s\S]{0,180}?)(?:@|Max\.\s*torque)",
            context,
            re.IGNORECASE,
        )
        torque_match = re.search(
            r"(?:Max\.\s*)?torque\s+([\s\S]{0,180}?)(?:@|Transmission)",
            context,
            re.IGNORECASE,
        )
        powers = re.findall(r"\d+(?:\.\d+)?\s*PS", power_match.group(1), re.IGNORECASE) if power_match else []
        torques = re.findall(r"\d+(?:\.\d+)?\s*Nm", torque_match.group(1), re.IGNORECASE) if torque_match else []

        if not (engines or powers or torques):
            return ""

        response = f"### Powertrain — {car_name}\n"
        if engines:
            response += f"- **Engine options:** {', '.join(engines[:-1])}{' and ' if len(engines) > 1 else ''}{engines[-1]}.\n"
        if powers:
            response += f"- **Maximum power:** {', '.join(powers)} respectively.\n"
        if torques:
            response += f"- **Maximum torque:** {', '.join(torques)} respectively."
        return response.strip()

    @staticmethod
    def _brochure_model_facts(question: str, chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        question_lower = question.lower()
        include_all_models = RAGService._all_models_requested(question)
        models: Dict[str, Dict[str, Any]] = {}
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            model = str(metadata.get("model", "")).strip()
            brand = str(metadata.get("brand", "")).strip()
            if model and (
                include_all_models
                or re.search(rf"\b{re.escape(model.lower())}\b", question_lower)
            ):
                entry = models.setdefault(
                    model.lower(),
                    {"name": f"{brand} {model}".strip(), "text": []},
                )
                entry["text"].append(str(chunk.get("content", "")))

        ordered = sorted(models.items(), key=lambda item: question_lower.find(item[0]))
        facts: Dict[str, Dict[str, Any]] = {}
        for model, details in ordered:
            text = re.sub(r"\s+", " ", " ".join(details["text"]))
            dimensions = {}
            for field, label in (
                ("length", "overall length"),
                ("width", "overall width"),
                ("height", "overall height"),
                ("wheelbase", "wheelbase"),
            ):
                match = re.search(
                    rf"{label}\s*\(mm\)\s*(\d+(?:[\s,]+\d{{3}})?)",
                    text,
                    re.IGNORECASE,
                )
                if match:
                    dimensions[field] = int(re.sub(r"\D", "", match.group(1)))

            boot_match = re.search(
                r"boot\s+space\s*(?:\(\s*l\s*\))?\s*:?\s*"
                r"([\d,]+(?:\*{1,2})?(?:\s+[\d,]+(?:\*{1,2})?)*)",
                text,
                re.IGNORECASE,
            )
            boot_capacities = (
                [int(value.replace(",", "")) for value in re.findall(r"\d[\d,]*", boot_match.group(1))]
                if boot_match
                else []
            )
            engines = list(dict.fromkeys(
                match.group(0)
                for match in re.finditer(
                    r"1\.5\s*l\s*(?:U2\s+CRDi|Turbo\s+GDi|MPi)\s*(?:petrol|diesel)",
                    text,
                    re.IGNORECASE,
                )
            ))
            facts[model] = {
                "name": details["name"],
                "dimensions": dimensions,
                "boot_capacities": boot_capacities,
                "engines": engines,
            }
        return facts

    @staticmethod
    def _format_mm(value: int) -> str:
        return f"{value:,} mm"

    @staticmethod
    def _comparison_feature_evidence(
        question: str,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, List[str]]:
        category_terms = {
            "Safety": (
                "safety", "airbag", "abs", "esc", "adas", "braking", "isofix",
                "camera", "collision", "stability", "seat belt", "seatbelt",
            ),
            "Technology": (
                "touchscreen", "infotainment", "audio", "speaker", "connected",
                "navigation", "android auto", "apple carplay", "display", "wireless", "usb",
                "remote vehicle controls", "remote engine start",
            ),
            "Comfort & convenience": (
                "seat", "sunroof", "ventilat", "climate", "air conditioning", "cruise",
                "keyless", "boot", "space", "recline", "charging", "comfort",
            ),
            "Exterior & dimensions": (
                "length", "width", "height", "wheelbase", "ground clearance",
                "alloy", "headlamp", "led", "grille", "outside mirror", "orvm", "exterior",
            ),
            "Price & warranty": ("price", "cost", "warranty", "inr", "ex-showroom"),
            "Powertrain": (
                "engine", "torque", "transmission", "gearbox",
                "petrol", "diesel", "fuel", "range", "mileage", "hybrid",
            ),
        }
        question_lower = question.lower()
        selected_categories = [
            category for category, terms in category_terms.items()
            if any(term in question_lower for term in terms)
        ]
        if not selected_categories or re.search(
            r"\b(features?|equipment|all|every|each)\b",
            question_lower,
        ):
            selected_categories = list(category_terms)

        evidence_candidates: Dict[str, List[Dict[str, Any]]] = {}
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            text = re.sub(
                r"(?m)^\s*(?:Vehicle|Document):[^\n]*(?:\n|$)",
                "",
                str(chunk.get("content", "")),
            ).replace("•", "\n")
            fragments = []
            for line in text.replace("|", "\n").splitlines():
                fragments.extend(re.split(r"(?<=[.!?])\s+|;\s+", line.strip()))

            for fragment in fragments:
                point = re.sub(r"\s+", " ", fragment).strip(" \t-*")
                if len(point) < 20:
                    continue
                point_lower = point.lower()
                if re.search(
                    r"\b(disclaimer|recommends?|advised|please refer|owner'?s manual|"
                    r"terms and conditions|representation purpose|not be provided|"
                    r"not a standard|customer needs to purchase|more about the functioning|"
                    r"depends upon various factors|symphony of|stand above it all|"
                    r"designed to strike a balance|stay completely connected)\b",
                    point_lower,
                ):
                    continue
                if (
                    not re.search(r"\d", point)
                    and len(point.split()) <= 4
                    and re.search(r"\b(capacity|transmission|dimensions)\b|power train", point_lower)
                ):
                    continue

                def matches_category(name: str, terms: tuple[str, ...]) -> bool:
                    if name == "Powertrain" and re.search(
                        r"\bremote\b.{0,40}\b(?:engine|start)\b",
                        point_lower,
                    ):
                        return False
                    if any(
                        re.search(rf"\b{re.escape(term)}s?\b", point_lower)
                        for term in terms
                        if term != "ventilat"
                    ):
                        return True
                    if name == "Comfort & convenience" and re.search(
                        r"\bventilat\w*\b",
                        point_lower,
                    ):
                        return True
                    if name == "Powertrain" and re.search(
                        r"\bpower\b.{0,40}\b(?:bhp|ps|kw)\b|\b(?:bhp|ps|kw)\b.{0,40}\bpower\b",
                        point_lower,
                    ):
                        return True
                    motor_spec = (
                        name == "Powertrain"
                        and re.search(r"\bmotor\b", point_lower)
                        and re.search(
                            r"\b(electric|battery|powertrain|torque|bhp|ps|kw|nm)\b",
                            point_lower,
                        )
                    )
                    battery_spec = (
                        name == "Powertrain"
                        and re.search(r"\bbattery\b", point_lower)
                        and re.search(
                            r"\b(electric vehicle|ev|kwh|battery capacity|battery pack)\b",
                            point_lower,
                        )
                    )
                    return bool(motor_spec or battery_spec)

                category = next(
                    (
                        name for name, terms in category_terms.items()
                        if name in selected_categories
                        and matches_category(name, terms)
                    ),
                    None,
                )
                if category is None:
                    continue
                if len(point) > 280:
                    point = point[:277].rsplit(" ", 1)[0].rstrip(" ,;:-") + "..."
                page = metadata.get("page")
                if page:
                    point = f"{point} (brochure p. {page})"
                candidates = evidence_candidates.setdefault(category, [])
                point_key = re.sub(
                    r"\s*\(brochure p\.\s*\d+\)$",
                    "",
                    point,
                    flags=re.IGNORECASE,
                ).casefold()
                if all(candidate["key"] != point_key for candidate in candidates):
                    score = sum(
                        bool(re.search(rf"\b{re.escape(term)}\b", point_lower))
                        for term in category_terms[category]
                        if term != "ventilat"
                    )
                    if re.search(r"\d", point):
                        score += 2
                    if re.search(r"\b(adas|airbags?|abs|esc|sunroof|touchscreen)\b", point_lower):
                        score += 2
                    candidates.append({"score": score, "key": point_key, "point": point})

        return {
            category: [
                candidate["point"]
                for candidate in sorted(candidates, key=lambda candidate: candidate["score"], reverse=True)[:3]
            ]
            for category, candidates in evidence_candidates.items()
        }

    @staticmethod
    def _compare_from_brochures(question: str, chunks: List[Dict[str, Any]]) -> str:
        models = RAGService._brochure_model_facts(question, chunks)
        if len(models) < 2:
            return "I couldn't retrieve comparable brochure specifications for both models."
        evidence_by_model = {
            model: RAGService._comparison_feature_evidence(
                question,
                [
                    chunk for chunk in chunks
                    if str(chunk.get("metadata", {}).get("model", "")).strip().lower() == model
                ],
            )
            for model in models
        }
        response = []
        categories = list(dict.fromkeys(
            category
            for evidence in evidence_by_model.values()
            for category in evidence
        ))
        for category in categories:
            category_rows = []
            for model, details in models.items():
                facts = evidence_by_model[model].get(category, [])
                if facts:
                    category_rows.append(
                        f"- **{details['name']}:** {'; '.join(facts)}"
                    )
            if category_rows:
                response.extend([f"### {category}", *category_rows])

        if len(models) > 2:
            if not response:
                return "The retrieved brochure passages don't contain feature details for these models."
            response.append(
                "Feature availability can vary by trim; these points reflect only the retrieved brochure passages."
            )
            return "\n".join(response)

        first, second = list(models.values())[:2]
        shared_dimensions = [
            field for field in ("length", "width", "wheelbase")
            if field in first["dimensions"] and field in second["dimensions"]
        ]
        if shared_dimensions:
            def dimension_summary(model: Dict[str, Any]) -> str:
                details = []
                if "length" in model["dimensions"]:
                    details.append(f"length {RAGService._format_mm(model['dimensions']['length'])}")
                if "width" in model["dimensions"]:
                    details.append(f"width {RAGService._format_mm(model['dimensions']['width'])}")
                if "wheelbase" in model["dimensions"]:
                    details.append(f"wheelbase {RAGService._format_mm(model['dimensions']['wheelbase'])}")
                return "; ".join(details)

            response.extend([
                "### Dimensions",
                f"- **{first['name']}:** {dimension_summary(first)}.",
                f"- **{second['name']}:** {dimension_summary(second)}.",
            ])
            first_wins = sum(
                first["dimensions"][field] > second["dimensions"][field]
                for field in shared_dimensions
            )
            second_wins = sum(
                second["dimensions"][field] > first["dimensions"][field]
                for field in shared_dimensions
            )
            if first_wins == len(shared_dimensions):
                response.append(
                    f"- {first['name']} has larger values on the comparable exterior measures; these don't "
                    "establish usable cabin space."
                )
            elif second_wins == len(shared_dimensions):
                response.append(
                    f"- {second['name']} has larger values on the comparable exterior measures; these don't "
                    "establish usable cabin space."
                )
            else:
                response.append(
                    "- The exterior measurements differ by model; they don't establish usable cabin space."
                )

        if first["engines"] and second["engines"]:
            response.extend([
                "### Brochure-listed engine options",
                f"- **{first['name']}:** {', '.join(first['engines'])}.",
                f"- **{second['name']}:** {', '.join(second['engines'])}.",
            ])
        if first["boot_capacities"] and second["boot_capacities"]:
            first_boot = " / ".join(f"{value} L" for value in first["boot_capacities"])
            second_boot = " / ".join(f"{value} L" for value in second["boot_capacities"])
            response.extend([
                "### Boot capacity",
                f"- **{first['name']}:** {first_boot}.",
                f"- **{second['name']}:** {second_boot}.",
            ])

        if not response:
            return "The retrieved brochure passages don't contain feature details for these models."
        response.append(
            "Feature availability can vary by trim; these points reflect only the retrieved brochure passages."
        )
        return "\n".join(response)

    @staticmethod
    def _recommend_from_brochures(question: str, chunks: List[Dict[str, Any]]) -> str:
        question_lower = question.lower()
        if not any(term in question_lower for term in ("space", "room", "boot", "luggage", "cargo")):
            return ""
        models = RAGService._brochure_model_facts(question, chunks)
        if len(models) < 2:
            return ""
        first_key, second_key = list(models)[:2]
        first, second = models[first_key], models[second_key]

        if first["boot_capacities"] and second["boot_capacities"]:
            first_boot = max(first["boot_capacities"])
            second_boot = max(second["boot_capacities"])
            if first_boot == second_boot:
                return (
                    f"The brochures list the same maximum boot capacity ({first_boot} L) for "
                    f"**{first['name']}** and **{second['name']}**; they don't establish a winner for overall space."
                )
            winner, other = (first, second) if first_boot > second_boot else (second, first)
            winner_capacities = " / ".join(f"{value} L" for value in winner["boot_capacities"])
            other_capacities = " / ".join(f"{value} L" for value in other["boot_capacities"])
            return (
                f"### Better for documented boot space: {winner['name']}\n"
                f"- The brochures list **{winner_capacities}** for {winner['name']} and "
                f"**{other_capacities}** for {other['name']}.\n"
                f"- {winner['name']} has the larger listed boot figure; this doesn't determine passenger-cabin room."
            )

        common_dimensions = [
            field for field in ("length", "wheelbase")
            if field in first["dimensions"] and field in second["dimensions"]
        ]
        if common_dimensions:
            first_wins = sum(first["dimensions"][field] > second["dimensions"][field] for field in common_dimensions)
            second_wins = sum(second["dimensions"][field] > first["dimensions"][field] for field in common_dimensions)
            if first_wins != second_wins:
                winner, other = (first, second) if first_wins > second_wins else (second, first)
                metrics = [
                    f"{RAGService._format_mm(winner['dimensions'][field])} vs "
                    f"{RAGService._format_mm(other['dimensions'][field])} {field}"
                    for field in common_dimensions
                ]
                return (
                    f"### Better for exterior size: {winner['name']}\n"
                    f"- The brochures list {', '.join(metrics)} for {winner['name']} and "
                    f"{other['name']} respectively.\n"
                    "- This indicates a larger exterior footprint, not necessarily more usable cabin or boot space."
                )
            return (
                "The retrieved exterior dimensions don't consistently favor either model, and the brochure "
                "passages don't provide comparable cabin or boot measurements."
            )

        return (
            "The retrieved brochure passages don't provide comparable boot or dimension figures, "
            "so I can't make a brochure-backed space recommendation."
        )

rag_service = RAGService()
