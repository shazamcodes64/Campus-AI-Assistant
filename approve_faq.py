# approve_faq.py
import json
from pathlib import Path
from datetime import datetime

from contradiction_detector import detect_contradictions

PROMOTION_QUEUE = Path("logs/promotion_queue.jsonl")
FAQ_FILE = Path("data/faq.json")
AUDIT_LOG = Path("logs/admin_audit.jsonl")

AUTO_APPROVE_CONFIDENCE = 0.95


# ------------------ UTILITIES ------------------

def load_jsonl(path: Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path: Path, record: dict):
    path.parent.mkdir(exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_faq():
    if not FAQ_FILE.exists():
        return []
    with open(FAQ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_faq(faq_data):
    FAQ_FILE.parent.mkdir(exist_ok=True)
    with open(FAQ_FILE, "w", encoding="utf-8") as f:
        json.dump(faq_data, f, indent=2)


def audit(action: str, candidate: dict, reason: str):
    append_jsonl(AUDIT_LOG, {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "question": candidate["query"],
        "confidence": candidate.get("confidence"),
        "reason": reason,
        "admin": "local_cli"
    })


# ------------------ MAIN FLOW ------------------

def approve():
    candidates = load_jsonl(PROMOTION_QUEUE)

    if not candidates:
        print("✅ No pending promotion candidates.")
        return

    faq_data = load_faq()

    print(f"\n🔍 {len(candidates)} promotion candidates found.\n")

    for idx, candidate in enumerate(candidates):
        print("=" * 60)
        print(f"[{idx}] QUESTION:")
        print(candidate["query"])
        print("\nANSWER:")
        print(candidate["answer"])
        print(f"\nConfidence: {candidate.get('confidence')}")
        print(f"Source docs used: {candidate.get('source_docs')}")

        # -------- CONTRADICTION CHECK --------
        contradictions = detect_contradictions(
            candidate["query"],
            candidate["answer"]
        )

        hard_conflict = any(c["type"] == "hard" for c in contradictions)

        if hard_conflict:
            print("\n❌ HARD CONTRADICTION DETECTED — AUTO REJECTED")
            audit("rejected", candidate, "hard_contradiction")
            continue

        # -------- FAST AUTO-APPROVAL --------
        if candidate.get("confidence", 0) >= AUTO_APPROVE_CONFIDENCE:
            faq_data.append({
                "question": candidate["query"],
                "answer": candidate["answer"],
                "verified": True
            })
            audit("auto_approved", candidate, "high_confidence_no_conflict")
            print("⚡ Auto-approved (high confidence, no conflict)")
            continue

        # -------- SOFT CONTRADICTION WARNING --------
        if contradictions:
            print("\n⚠️ POSSIBLE CONTRADICTIONS:\n")
            for c in contradictions:
                print("Existing question:")
                print(c["existing_question"])
                print("Existing answer:")
                print(c["existing_answer"])
                print(
                    f"Q similarity: {c['question_similarity']:.2f} | "
                    f"A similarity: {c['answer_similarity']:.2f}"
                )
                print("-" * 40)

        # -------- MANUAL DECISION --------
        decision = input("\nApprove this FAQ? (y/n/q): ").strip().lower()

        if decision == "y":
            faq_data.append({
                "question": candidate["query"],
                "answer": candidate["answer"],
                "verified": True
            })
            audit("approved", candidate, "manual_approval")
            print("✅ Approved & added to FAQ.")

        elif decision == "q":
            print("⏹ Exiting.")
            break

        else:
            audit("rejected", candidate, "manual_reject")
            print("❌ Skipped.")

    save_faq(faq_data)
    print("\n📦 FAQ file updated.")


if __name__ == "__main__":
    approve()
