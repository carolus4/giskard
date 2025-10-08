#!/usr/bin/env python3
"""
Command-line tool for managing prompts and viewing performance metrics
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.prompt_registry import prompt_registry
from utils.prompt_performance_tracker import performance_tracker, PerformanceMetrics


def list_prompts():
    """List all available prompts"""
    prompts = prompt_registry.list_prompts()
    if not prompts:
        print("No prompts found in registry.")
        return
    
    print("Available prompts:")
    print("-" * 50)
    for prompt_name in prompts:
        versions = prompt_registry.get_prompt_versions(prompt_name)
        print(f"{prompt_name}:")
        for version in versions:
            print(f"  v{version.version}")
            print(f"    Created: {version.created_at.strftime('%Y-%m-%d %H:%M') if version.created_at else 'Unknown'}")
        print()


def show_prompt_details(prompt_name: str, version: str = None):
    """Show detailed information about a specific prompt"""
    prompt_config = prompt_registry.get_prompt_config(prompt_name, version)
    if not prompt_config:
        print(f"Prompt '{prompt_name}' not found.")
        return
    
    print(f"Prompt: {prompt_config['name']} v{prompt_config['version']}")
    print("=" * 60)
    print(f"Goal: {prompt_config.get('goal', 'N/A')}")
    print(f"Model: {prompt_config.get('model', 'N/A')}")
    print(f"Temperature: {prompt_config.get('temperature', 'N/A')}")
    print(f"Token Limit: {prompt_config.get('token_limit', 'N/A')}")
    print(f"Top-P: {prompt_config.get('top_p', 'N/A')}")
    print(f"Created: {prompt_config.get('created_at', 'Unknown')}")
    print()
    print("Prompt Text:")
    print("-" * 40)
    print(prompt_config.get('text', 'N/A'))
    print()


def show_performance(prompt_name: str, days: int = 30):
    """Show performance metrics for a prompt"""
    summary = performance_tracker.get_performance_summary(prompt_name, days)
    
    if summary.get("total_executions", 0) == 0:
        print(f"No performance data found for '{prompt_name}' in the last {days} days.")
        return
    
    print(f"Performance Summary for '{prompt_name}' (last {days} days)")
    print("=" * 60)
    print(f"Total Executions: {summary['total_executions']}")
    print(f"Successful Executions: {summary['successful_executions']}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    
    if summary.get('average_execution_time_ms'):
        print(f"Average Execution Time: {summary['average_execution_time_ms']:.1f}ms")
    
    if summary.get('average_output_length'):
        print(f"Average Output Length: {summary['average_output_length']:.0f} characters")
    
    if summary.get('average_quality_score'):
        print(f"Average Quality Score: {summary['average_quality_score']:.1f}/10")
    
    print(f"First Execution: {summary.get('first_execution', 'Unknown')}")
    print(f"Latest Execution: {summary.get('latest_execution', 'Unknown')}")
    print()


def compare_versions(prompt_name: str):
    """Compare performance across different versions of a prompt"""
    comparison = performance_tracker.get_version_comparison(prompt_name)
    
    if not comparison:
        print(f"No performance data found for '{prompt_name}'.")
        return
    
    print(f"Version Comparison for '{prompt_name}'")
    print("=" * 80)
    print(f"{'Version':<15} {'Executions':<12} {'Success Rate':<12} {'Avg Time (ms)':<15} {'Avg Length':<12}")
    print("-" * 80)
    
    for version, metrics in comparison.items():
        success_rate = f"{metrics['success_rate']:.1%}" if metrics['success_rate'] is not None else "N/A"
        avg_time = f"{metrics['average_execution_time_ms']:.1f}" if metrics['average_execution_time_ms'] else "N/A"
        avg_length = f"{metrics['average_output_length']:.0f}" if metrics['average_output_length'] else "N/A"
        
        print(f"{version:<15} {metrics['total_executions']:<12} {success_rate:<12} {avg_time:<15} {avg_length:<12}")
    print()


def show_trends(prompt_name: str, days: int = 30):
    """Show performance trends over time"""
    trends = performance_tracker.get_trend_analysis(prompt_name, days)
    
    if trends.get('insufficient_data'):
        print(f"Insufficient data for trend analysis of '{prompt_name}'.")
        return
    
    print(f"Trend Analysis for '{prompt_name}' (last {days} days)")
    print("=" * 60)
    print(f"Total Executions: {trends['total_executions']}")
    print(f"Overall Trend: {trends['overall_trend']}")
    
    if trends.get('daily_success_rates'):
        recent_success = trends['daily_success_rates'][-1] if trends['daily_success_rates'] else 0
        print(f"Most Recent Success Rate: {recent_success:.1%}")
    
    if trends.get('daily_avg_times'):
        recent_time = trends['daily_avg_times'][-1] if trends['daily_avg_times'] else 0
        print(f"Most Recent Avg Time: {recent_time:.1f}ms")
    print()


def create_new_prompt():
    """Interactive prompt creation"""
    print("Create New Prompt")
    print("=" * 30)
    print("Note: This creates a new prompt text file. Metadata (model, temperature, etc.)")
    print("should be added to config/prompt_registry.py manually.")
    print()
    
    name = input("Prompt name: ").strip()
    if not name:
        print("Prompt name is required.")
        return
    
    version = input("Version (default: 1.0): ").strip() or "1.0"
    
    print("\nEnter the prompt text (end with a line containing only 'END'):")
    prompt_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        prompt_lines.append(line)
    
    prompt_text = "\n".join(prompt_lines)
    if not prompt_text.strip():
        print("Prompt text is required.")
        return
    
    # Save the prompt text file
    try:
        file_path = prompt_registry.save_prompt(name, version, prompt_text)
        print(f"\nPrompt text saved successfully: {file_path}")
        print("\nNext steps:")
        print("1. Add metadata to config/prompt_registry.py in the _prompt_metadata dict")
        print("2. Include goal, model, temperature, token_limit, and top_p settings")
    except Exception as e:
        print(f"Error creating prompt: {e}")


def export_data(prompt_name: str = None, format: str = "json"):
    """Export performance data"""
    data = performance_tracker.export_performance_data(prompt_name, format)
    
    if format == "json":
        filename = f"prompt_performance_{prompt_name or 'all'}.json"
    else:
        filename = f"prompt_performance_{prompt_name or 'all'}.csv"
    
    with open(filename, 'w') as f:
        f.write(data)
    
    print(f"Performance data exported to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Manage prompts and view performance metrics")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List prompts
    subparsers.add_parser('list', help='List all available prompts')
    
    # Show prompt details
    show_parser = subparsers.add_parser('show', help='Show prompt details')
    show_parser.add_argument('prompt_name', help='Name of the prompt')
    show_parser.add_argument('--version', help='Specific version to show')
    
    # Show performance
    perf_parser = subparsers.add_parser('performance', help='Show performance metrics')
    perf_parser.add_argument('prompt_name', help='Name of the prompt')
    perf_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    
    # Compare versions
    comp_parser = subparsers.add_parser('compare', help='Compare prompt versions')
    comp_parser.add_argument('prompt_name', help='Name of the prompt')
    
    # Show trends
    trend_parser = subparsers.add_parser('trends', help='Show performance trends')
    trend_parser.add_argument('prompt_name', help='Name of the prompt')
    trend_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    
    # Create new prompt
    subparsers.add_parser('create', help='Create a new prompt')
    
    # Export data
    export_parser = subparsers.add_parser('export', help='Export performance data')
    export_parser.add_argument('--prompt', help='Specific prompt to export')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'list':
            list_prompts()
        elif args.command == 'show':
            show_prompt_details(args.prompt_name, args.version)
        elif args.command == 'performance':
            show_performance(args.prompt_name, args.days)
        elif args.command == 'compare':
            compare_versions(args.prompt_name)
        elif args.command == 'trends':
            show_trends(args.prompt_name, args.days)
        elif args.command == 'create':
            create_new_prompt()
        elif args.command == 'export':
            export_data(args.prompt, args.format)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
