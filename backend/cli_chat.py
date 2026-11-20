import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.services.rag_service import rag_service
from app.services.comparison_service import comparison_service

def print_banner():
    print("=" * 70)
    print("       🚗 AUTOMOTIVE AI ASSISTANT - INTERACTIVE CHATBOT 🚗")
    print("=" * 70)
    print("Knowledge Source: Official Brochures (Creta, Alcazar, Seltos, Nexon)")
    print("Type your automotive questions below. (Type 'exit' or 'quit' to stop)\n")
    print("Sample Questions to Try:")
    print("  1. What are the engine options and power outputs of Hyundai Creta?")
    print("  2. Compare Hyundai Alcazar vs Hyundai Creta in seating and dimensions.")
    print("  3. What safety features and airbags are available in Tata Nexon?")
    print("  4. compare: Kia Seltos vs Hyundai Creta")
    print("-" * 70 + "\n")

def main():
    print_banner()
    session_id = None

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nExiting chatbot. Goodbye!")
                break

            # Check if user wants a direct comparison command
            if user_input.lower().startswith("compare:"):
                raw_cars = user_input[8:].strip()
                if " vs " in raw_cars.lower():
                    parts = raw_cars.split(" vs ")
                    car_a, car_b = parts[0].strip(), parts[1].strip()
                    print(f"\n🔄 Generating side-by-side comparison for {car_a} vs {car_b}...\n")
                    res = comparison_service.compare_cars(car_a, car_b)
                    print(f"\nAssistant:\n{res['summary']}\n")
                    print("-" * 50)
                    print("📚 Source References:")
                    for s in res["sources"]:
                        print(f"  • [{s['document']} | Page {s['page']} | {s['section']}]")
                        print(f"    Excerpt: \"{s['excerpt'][:120]}...\"\n")
                    continue

            # Standard RAG Query
            print("\n🔄 Searching brochures & generating response...\n")
            res = rag_service.query(user_query=user_input, session_id=session_id)
            session_id = res.get("session_id")

            print(f"Assistant:\n{res['answer']}\n")

            if res.get("sources"):
                print("-" * 50)
                print("📚 Source References (Brochure Citations):")
                for s in res["sources"]:
                    print(f"  • [{s['document']} | Page {s['page']} | {s['section']}]")
                    print(f"    Excerpt: \"{s['excerpt'][:120]}...\"\n")

        except KeyboardInterrupt:
            print("\nExiting chatbot. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error processing question: {e}")

if __name__ == "__main__":
    main()
