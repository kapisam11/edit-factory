#!/usr/bin/env python3
"""Quick demo: AI Video Factory Learning System.

This script demonstrates how to use the new 2026 learning system
to create video edits for any topic.

Run with:
  python demo_learning_system.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_video_factory.knowledge import KnowledgeBase, RequestProcessor
from ai_video_factory.request_handler import AIVideoFactoryRequest


def demo_1_knowledge_base():
    """Demo 1: Show what the system knows."""
    print("=" * 70)
    print("DEMO 1: What Does the System Know?")
    print("=" * 70)
    print()

    kb = KnowledgeBase()

    print("EDITING PATTERNS (2026 Standards):")
    print()
    print("Good editing includes:")
    for i, pattern in enumerate(kb.editing_patterns["good_editing"][:5], 1):
        print(f"  {i}. {pattern}")
    print()

    print("Trendy techniques right now:")
    for i, effect in enumerate(kb.editing_patterns["trendy_2026"][:5], 1):
        print(f"  {i}. {effect}")
    print()


def demo_2_topics():
    """Demo 2: Show topic expertise."""
    print("=" * 70)
    print("DEMO 2: Topic Expertise (What to Emphasize)")
    print("=" * 70)
    print()

    kb = KnowledgeBase()

    for topic_name in ["minecraft", "roblox", "cod"]:
        expertise = kb.get_topic_expertise(topic_name)
        print(f"{topic_name.upper()}:")
        print(f"  Tone: {expertise.get('tone')}")
        print(f"  Key elements: {', '.join(expertise.get('key_elements', [])[:3])}")
        print(f"  Best hooks: {', '.join(expertise.get('best_hooks', [])[:2])}")
        print()


def demo_3_request_validation():
    """Demo 3: Show request validation."""
    print("=" * 70)
    print("DEMO 3: Request Validation (What's Possible)")
    print("=" * 70)
    print()

    processor = RequestProcessor()

    test_cases = [
        ("Minecraft", "make a betrayal edit", True),
        ("Roblox", "create an obby challenge video", True),
        ("COD", "make a 1v5 clutch compilation", True),
        ("", "make a video", False),  # Invalid
        ("Minecraft", "blah blah", False),  # Invalid
        ("Fortnite", "make a building guide", True),  # Auto-inferred
    ]

    for topic, request, should_work in test_cases:
        success, msg, context = processor.process_request(topic, request)
        status = "VALID" if success else "INVALID"
        print(f"[{status}] {topic:15} | {request:40}")
        if not success:
            print(f"        Reason: {msg}")
    print()


def demo_4_trending_knowledge():
    """Demo 4: Show trending knowledge."""
    print("=" * 70)
    print("DEMO 4: 2026 Trending Knowledge")
    print("=" * 70)
    print()

    kb = KnowledgeBase()
    trending = kb.get_trending_techniques()

    print("Optimal Video Specs:")
    print(f"  Length: {trending.get('viral_length')}")
    print(f"  Cuts per minute: {trending.get('optimal_cuts_per_minute')}")
    print(f"  Average shot duration: {trending.get('average_shot_duration')}s")
    print(f"  Hook placement: {trending.get('hook_placement')}")
    print(f"  Climax position: {trending.get('climax_position')}")
    print()

    print("Algorithm Preferences (2026):")
    for metric, importance in trending.get("algorithm_preferences_2026", {}).items():
        print(f"  {metric:20} {importance}")
    print()


def demo_5_filter_effectiveness():
    """Demo 5: Show which filters work best."""
    print("=" * 70)
    print("DEMO 5: Filter Effectiveness Ratings")
    print("=" * 70)
    print()

    kb = KnowledgeBase()

    print("Filter effectiveness scores (0.0-1.0):")
    for filter_name, data in sorted(kb.filter_effectiveness.items(), key=lambda x: -x[1].get("effectiveness", 0)):
        eff = data.get("effectiveness", 0)
        success_rate = data.get("success_rate", 0)
        uses = data.get("uses", 0)
        print(f"  {filter_name:25} {eff:.2f} (success: {success_rate:.0%}, used {uses}x)")
    print()


def demo_6_creating_edits():
    """Demo 6: Show how to create edits."""
    print("=" * 70)
    print("DEMO 6: How to Create Video Edits")
    print("=" * 70)
    print()

    print("Method 1: CLI Tool")
    print("  python make_edit.py 'Minecraft' 'make a betrayal edit'")
    print()

    print("Method 2: Python API (Simple)")
    print("  from ai_video_factory.request_handler import create_edit")
    print("  success, msg, pkg_dir = create_edit('Minecraft', 'make a betrayal edit')")
    print()

    print("Method 3: Python API (Advanced)")
    print("  from ai_video_factory.request_handler import AIVideoFactoryRequest")
    print("  factory = AIVideoFactoryRequest()")
    print("  success, msg, pkg_dir = factory.create_edit(")
    print("      'Minecraft', 'make a betrayal edit',")
    print("      target_seconds=60,")
    print("      use_groq=True")
    print("  )")
    print("  if success:")
    print("      factory.learn_from_feedback(pkg_dir, engagement_score=0.85)")
    print()


def demo_7_learning_loop():
    """Demo 7: Show learning capability."""
    print("=" * 70)
    print("DEMO 7: Learning from Feedback")
    print("=" * 70)
    print()

    print("The system learns what works:")
    print()
    print("1. Create an edit")
    print("   factory.create_edit('COD', 'make a 1v5 clutch')")
    print()
    print("2. Track engagement (0.0-1.0)")
    print("   factory.learn_from_feedback(pkg_dir, engagement_score=0.92)")
    print()
    print("3. Improve automatically")
    print("   Next COD edit uses learned insights for better results")
    print()

    print("Learning is persistent in: knowledge_base/")
    print("  - editing_patterns.json")
    print("  - topic_expertise.json")
    print("  - filter_effectiveness.json")
    print("  - request_history.json")
    print()


def demo_8_error_handling():
    """Demo 8: Show graceful error handling."""
    print("=" * 70)
    print("DEMO 8: Error Handling (Graceful Failures)")
    print("=" * 70)
    print()

    processor = RequestProcessor()

    bad_requests = [
        ("", "anything"),
        ("TopicXYZ", "irrelevant"),
        ("Minecraft", "xyzabc"),
    ]

    print("Invalid requests get helpful error messages:")
    print()
    for topic, request in bad_requests:
        success, msg, context = processor.process_request(topic, request)
        if not success:
            print(f"User request: create_edit('{topic}', '{request}')")
            print(f"System response: {msg[:70]}...")
            print()


def main():
    """Run all demos."""
    print()
    print("*" * 70)
    print("AI VIDEO FACTORY: 2026 LEARNING SYSTEM DEMO")
    print("*" * 70)
    print()

    demos = [
        ("Knowledge Base", demo_1_knowledge_base),
        ("Topic Expertise", demo_2_topics),
        ("Request Validation", demo_3_request_validation),
        ("Trending Knowledge", demo_4_trending_knowledge),
        ("Filter Effectiveness", demo_5_filter_effectiveness),
        ("Creating Edits", demo_6_creating_edits),
        ("Learning Loop", demo_7_learning_loop),
        ("Error Handling", demo_8_error_handling),
    ]

    for i, (name, func) in enumerate(demos, 1):
        try:
            func()
        except Exception as e:
            print(f"ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()

    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Try: python make_edit.py 'Minecraft' 'make a betrayal edit'")
    print("  2. Read: LEARNING_SYSTEM.md (comprehensive documentation)")
    print("  3. Integrate into your workflow!")
    print()


if __name__ == "__main__":
    main()
