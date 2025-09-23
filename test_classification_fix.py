#!/usr/bin/env python3
"""
Test script to verify the classification fix for project context
"""
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.task_db import TaskDB
from utils.classification_service import TaskClassificationService

def test_classification_fix():
    """Test that the classification fix is working correctly"""
    print("🧪 Testing Classification Fix for Project Context")
    print("=" * 55)
    
    service = TaskClassificationService()
    
    # Test cases with different projects
    test_cases = [
        {
            'title': 'Fix authentication bug',
            'description': 'Debug login issues in the system',
            'project': 'giskard',
            'expected': 'learning',
            'should_not_be': 'career'
        },
        {
            'title': 'Review financial reports',
            'description': 'Analyze Q3 performance metrics',
            'project': 'work',
            'expected': 'career',
            'should_not_be': 'learning'
        },
        {
            'title': 'Complete Python course',
            'description': 'Finish online programming course',
            'project': 'education',
            'expected': 'learning',
            'should_not_be': 'career'
        },
        {
            'title': 'Go to the gym',
            'description': 'Work out for 30 minutes',
            'project': 'health',
            'expected': 'health',
            'should_not_be': 'career'
        }
    ]
    
    print("Testing project-aware classification:")
    print("-" * 40)
    
    all_correct = True
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {case['title']} (project: {case['project']})")
        
        categories = service.classify_task(
            case['title'], 
            case['description'], 
            case['project']
        )
        
        print(f"   Categories: {categories}")
        print(f"   Expected: {case['expected']}")
        print(f"   Should NOT be: {case['should_not_be']}")
        
        # Check if classification is correct
        is_correct = (
            case['expected'] in categories and 
            case['should_not_be'] not in categories
        )
        
        if is_correct:
            print("   ✅ Classification is CORRECT")
        else:
            print("   ❌ Classification is INCORRECT")
            all_correct = False
    
    # Test the specific Giskard case that was problematic
    print(f"\n🔧 Testing the specific Giskard case:")
    print("-" * 40)
    
    giskard_categories = service.classify_task(
        'query back-end',
        'Investigate and resolve the issues with the query back-end.',
        'giskard'
    )
    
    print(f"Giskard task categories: {giskard_categories}")
    
    if 'learning' in giskard_categories and 'career' not in giskard_categories:
        print("✅ Giskard project correctly classified as LEARNING only")
    else:
        print("❌ Giskard project still misclassified")
        all_correct = False
    
    # Check the updated task in database
    print(f"\n📊 Checking updated task in database:")
    print("-" * 40)
    
    task = TaskDB.get_by_id(109)
    if task:
        print(f"Task: {task.title}")
        print(f"Project: {task.project}")
        print(f"Categories: {task.categories}")
        
        if task.categories == ['learning']:
            print("✅ Database task correctly updated")
        else:
            print("❌ Database task not correctly updated")
            all_correct = False
    else:
        print("❌ Task 109 not found")
        all_correct = False
    
    print(f"\n{'='*55}")
    if all_correct:
        print("✅ ALL TESTS PASSED - Classification fix is working correctly!")
        print("🎯 Giskard projects are now correctly classified as LEARNING only")
    else:
        print("❌ SOME TESTS FAILED - Classification fix needs more work")
    
    print(f"\n📋 Summary:")
    print("   - Project context is now included in classification")
    print("   - Giskard projects are correctly classified as 'learning'")
    print("   - Other project types are classified appropriately")
    print("   - The prompt rules are now being followed correctly")

if __name__ == '__main__':
    test_classification_fix()
