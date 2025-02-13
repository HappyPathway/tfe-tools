#!/usr/bin/env python3

import json
import sys
from typing import Dict, List, Tuple

def parse_tf_plan(plan_file: str) -> Tuple[List[str], List[str]]:
    """
    Parse terraform plan JSON output and return lists of resources to be created and destroyed.
    
    Args:
        plan_file (str): Path to the terraform plan JSON file
        
    Returns:
        Tuple containing two lists:
        - List of resources to be created
        - List of resources to be destroyed
    """
    with open(plan_file, 'r') as f:
        plan_data = json.load(f)

    to_create = []
    to_destroy = []

    # Get the resource changes from the plan
    resource_changes = plan_data.get('resource_changes', [])

    for change in resource_changes:
        address = change.get('address', '')
        change_type = change.get('change', {}).get('actions', [])
        
        if 'create' in change_type:
            to_create.append(address)
        elif 'delete' in change_type:
            to_destroy.append(address)

    return to_create, to_destroy

def main():
    if len(sys.argv) != 2:
        print("Usage: python parse_tf_plan.py <path_to_plan.json>")
        sys.exit(1)

    plan_file = sys.argv[1]
    try:
        to_create, to_destroy = parse_tf_plan(plan_file)
        
        if to_destroy:
            print("\nResources to be destroyed:")
            print("-" * 25)
            for resource in to_destroy:
                print(f"- {resource}")
                
        if to_create:
            print("\nResources to be created:")
            print("-" * 25)
            for resource in to_create:
                print(f"+ {resource}")
                
        if not to_create and not to_destroy:
            print("\nNo resources to be created or destroyed.")
            
    except FileNotFoundError:
        print(f"Error: Could not find plan file: {plan_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in plan file: {plan_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
