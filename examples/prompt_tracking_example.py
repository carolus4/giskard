#!/usr/bin/env python3
"""
Example script demonstrating the new prompt tracking system
"""

import sys
import os
import time
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.simple_prompt_registry import simple_prompt_registry
from utils.prompt_performance_tracker import performance_tracker, PerformanceMetrics


def simulate_prompt_execution(prompt_name: str, input_data: str, output: str, 
                            execution_time_ms: float = None, success: bool = True):
    """Simulate a prompt execution with performance tracking"""
    
    # Get the latest version of the prompt
    prompt_config = simple_prompt_registry.get_prompt_config(prompt_name)
    if not prompt_config:
        print(f"Prompt '{prompt_name}' not found!")
        return
    
    # Simulate execution time if not provided
    if execution_time_ms is None:
        execution_time_ms = 100 + (len(output) * 0.1)  # Rough simulation
    
    # Create performance metrics
    metrics = PerformanceMetrics(
        execution_time_ms=execution_time_ms,
        token_count=len(output.split()),  # Rough token count
        output_length=len(output),
        success=success,
        quality_score=8.5 if success else 3.0  # Simulated quality score
    )
    
    # Log the execution
    performance_tracker.log_execution(
        prompt_name=prompt_name,
        prompt_version=prompt_config['version'],
        output=output,
        metrics=metrics,
        input_data={"input": input_data}
    )
    
    print(f"✓ Logged execution of {prompt_name} v{prompt_config['version']}")
    print(f"  Input: {input_data[:50]}...")
    print(f"  Output: {output[:50]}...")
    print(f"  Execution time: {execution_time_ms:.1f}ms")
    print()


def demonstrate_prompt_tracking():
    """Demonstrate the prompt tracking system"""
    
    print("Prompt Tracking System Demo")
    print("=" * 50)
    
    # Show available prompts
    print("\n1. Available Prompts:")
    prompts = simple_prompt_registry.list_prompts()
    for prompt_name in prompts:
        versions = simple_prompt_registry.get_prompt_versions(prompt_name)
        print(f"  {prompt_name}: {len(versions)} version(s)")
        for version in versions:
            print(f"    v{version.version}")
    
    # Simulate some executions
    print("\n2. Simulating Prompt Executions:")
    
    # Simulate coaching prompt executions
    simulate_prompt_execution(
        "coaching_system",
        "I have 5 tasks due today and I'm feeling overwhelmed",
        "I understand that feeling overwhelmed with multiple tasks can be challenging. Let's break this down: First, prioritize your tasks by urgency and importance. Start with the most critical one and focus on completing it before moving to the next. Consider using the Pomodoro Technique - work for 25 minutes, then take a 5-minute break. This can help maintain focus and reduce overwhelm.",
        execution_time_ms=1200
    )
    
    simulate_prompt_execution(
        "coaching_system", 
        "I keep procrastinating on my project",
        "Procrastination often stems from feeling overwhelmed or uncertain about where to start. Try breaking your project into smaller, manageable tasks. Set a timer for just 10 minutes and commit to working on it - you'll often find you want to continue once you start. Also, identify what's causing the resistance - is it fear of failure, perfectionism, or lack of clarity?",
        execution_time_ms=950
    )
    
    # Simulate classification prompt executions
    simulate_prompt_execution(
        "task_classification",
        "Go to the gym for 30 minutes",
        '["health"]',
        execution_time_ms=150
    )
    
    simulate_prompt_execution(
        "task_classification",
        "Complete Python certification course",
        '["career", "learning"]',
        execution_time_ms=180
    )
    
    simulate_prompt_execution(
        "task_classification",
        "Buy groceries",
        '[]',
        execution_time_ms=120
    )
    
    # Show performance summaries
    print("\n3. Performance Summaries:")
    
    for prompt_name in prompts:
        summary = performance_tracker.get_performance_summary(prompt_name)
        if summary.get('total_executions', 0) > 0:
            print(f"\n{prompt_name}:")
            print(f"  Total Executions: {summary['total_executions']}")
            print(f"  Success Rate: {summary['success_rate']:.1%}")
            print(f"  Avg Execution Time: {summary.get('average_execution_time_ms', 0):.1f}ms")
            print(f"  Avg Output Length: {summary.get('average_output_length', 0):.0f} chars")
    
    # Show version comparison
    print("\n4. Version Comparison:")
    for prompt_name in prompts:
        comparison = performance_tracker.get_version_comparison(prompt_name)
        if comparison:
            print(f"\n{prompt_name}:")
            for version, metrics in comparison.items():
                print(f"  v{version}: {metrics['total_executions']} executions, "
                      f"{metrics['success_rate']:.1%} success rate")
    
    # Show trend analysis
    print("\n5. Trend Analysis:")
    for prompt_name in prompts:
        trends = performance_tracker.get_trend_analysis(prompt_name, days=7)
        if not trends.get('insufficient_data'):
            print(f"\n{prompt_name}:")
            print(f"  Trend: {trends['overall_trend']}")
            print(f"  Total Executions (7 days): {trends['total_executions']}")


def create_custom_prompt_example():
    """Example of creating a custom prompt"""
    
    print("\n6. Creating Custom Prompt Example:")
    
    # Create a new prompt for creative writing
    creative_prompt_text = """You are a creative writing assistant. Your job is to help writers overcome writer's block and generate engaging story ideas.

Guidelines:
- Be imaginative and original
- Provide specific, actionable writing prompts
- Consider different genres and styles
- Encourage experimentation and creativity
- Keep suggestions concise but inspiring

User's writing context: {writing_context}

Provide 3 creative writing prompts that match their context and interests."""
    
    # Save the prompt text file
    try:
        file_path = simple_prompt_registry.save_prompt("creative_writing", "1.0", creative_prompt_text)
        print(f"✓ Created custom prompt text file: {file_path}")
        print("Note: Add metadata to config/simple_prompt_registry.py manually")
    except Exception as e:
        print(f"Error creating prompt: {e}")
        return
    
    # Add metadata to the registry (this would normally be done manually in the config file)
    simple_prompt_registry.add_prompt_metadata("creative_writing", {
        "goal": "Generate creative and engaging story ideas and writing prompts",
        "model": "gemma3:4b",
        "temperature": 0.9,
        "token_limit": 300,
        "top_p": 0.95
    })
    
    # Simulate some executions
    simulate_prompt_execution(
        "creative_writing",
        "I want to write a sci-fi story but I'm stuck on the plot",
        "1. Write about a world where memories can be bought and sold - what happens when someone discovers their 'memories' are fake?\n2. A time traveler accidentally creates a paradox that splits reality into multiple timelines - explore the consequences.\n3. In a future where AI has achieved consciousness, a human and an AI must work together to solve a mystery that threatens both their species.",
        execution_time_ms=800
    )
    
    simulate_prompt_execution(
        "creative_writing",
        "I need inspiration for a fantasy novel",
        "1. A librarian discovers that the books in their care are actually portals to the worlds they describe - but some of those worlds are dangerous.\n2. In a world where magic is powered by emotions, a character who feels nothing must find a way to save their kingdom.\n3. A dragon who has lost their fire teams up with a human who has lost their voice to solve a mystery that threatens both their worlds.",
        execution_time_ms=750
    )


if __name__ == "__main__":
    try:
        demonstrate_prompt_tracking()
        create_custom_prompt_example()
        
        print("\n" + "=" * 50)
        print("Demo completed! Check the data/ directory for:")
        print("- prompt_performance.json (execution logs)")
        print("- prompt_metrics.json (cached metrics)")
        print("\nCheck the prompts/ directory for prompt text files")
        print("Use 'python scripts/prompt_manager.py list' to see all prompts")
        print("Use 'python scripts/prompt_manager.py performance <prompt_name>' to see metrics")
        
    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback
        traceback.print_exc()
