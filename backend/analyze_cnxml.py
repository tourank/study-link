#!/usr/bin/env python3
"""
Comprehensive analysis of CNXML structure to understand what we need to parse.

This script analyzes multiple modules to understand the full scope of educational
content we need to handle in our parser.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict, Counter
import json

def analyze_module(module_path):
    """Analyze a single module to understand its structure"""
    try:
        tree = ET.parse(module_path)
        root = tree.getroot()
        
        # Count all elements
        element_counts = Counter()
        
        # Track elements with important attributes
        elements_with_attrs = defaultdict(set)
        
        # Track section types
        section_types = defaultdict(int)
        
        def walk_elements(element, path=""):
            # Count this element
            element_counts[element.tag] += 1
            
            # Track attributes
            if element.attrib:
                for attr, value in element.attrib.items():
                    elements_with_attrs[element.tag].add(f"{attr}={value}")
            
            # Special handling for sections
            if element.tag.endswith('section'):
                section_class = element.get('class', 'regular')
                section_types[section_class] += 1
            
            # Recurse into children
            for child in element:
                walk_elements(child, path + "/" + element.tag.split("}")[-1])
        
        walk_elements(root)
        
        return {
            'element_counts': dict(element_counts),
            'elements_with_attrs': dict(elements_with_attrs),
            'section_types': dict(section_types)
        }
        
    except Exception as e:
        return {'error': str(e)}

def analyze_multiple_modules(base_path, num_modules=10):
    """Analyze multiple modules to get comprehensive understanding"""
    modules_dir = Path(base_path) / "modules"
    
    # Get a sample of modules
    module_dirs = list(modules_dir.glob("m66*"))[:num_modules]
    
    all_elements = Counter()
    all_attributes = defaultdict(set)
    all_section_types = Counter()
    
    print(f"Analyzing {len(module_dirs)} modules...")
    
    for i, module_dir in enumerate(module_dirs):
        module_file = module_dir / "index.cnxml"
        if module_file.exists():
            print(f"  {i+1}/{len(module_dirs)}: {module_dir.name}")
            
            analysis = analyze_module(module_file)
            
            if 'error' not in analysis:
                # Aggregate counts
                for element, count in analysis['element_counts'].items():
                    all_elements[element] += count
                
                # Aggregate attributes
                for element, attrs in analysis['elements_with_attrs'].items():
                    all_attributes[element].update(attrs)
                
                # Aggregate section types
                for section_type, count in analysis['section_types'].items():
                    all_section_types[section_type] += count
    
    return {
        'total_modules_analyzed': len(module_dirs),
        'element_counts': dict(all_elements),
        'elements_with_attributes': {k: sorted(list(v)) for k, v in all_attributes.items()},
        'section_types': dict(all_section_types)
    }

def categorize_elements(element_counts):
    """Categorize elements by their educational purpose"""
    categories = {
        'basic_content': [],
        'educational_structure': [],
        'exercises_assessment': [],
        'definitions_glossary': [],
        'media_figures': [],
        'navigation_links': [],
        'metadata': [],
        'formatting': []
    }
    
    # Clean element names (remove namespace)
    clean_elements = {}
    for element, count in element_counts.items():
        clean_name = element.split('}')[-1] if '}' in element else element
        clean_elements[clean_name] = count
    
    # Categorize elements
    for element, count in clean_elements.items():
        if element in ['para', 'content', 'title', 'emphasis', 'text']:
            categories['basic_content'].append((element, count))
        elif element in ['section', 'document', 'list', 'item', 'table', 'row', 'entry', 'note']:
            categories['educational_structure'].append((element, count))
        elif element in ['exercise', 'problem', 'solution', 'commentary']:
            categories['exercises_assessment'].append((element, count))
        elif element in ['definition', 'meaning', 'term', 'glossary']:
            categories['definitions_glossary'].append((element, count))
        elif element in ['figure', 'image', 'media', 'caption']:
            categories['media_figures'].append((element, count))
        elif element in ['link', 'target-id']:
            categories['navigation_links'].append((element, count))
        elif element in ['metadata', 'md:title', 'md:content-id', 'md:uuid', 'md:abstract']:
            categories['metadata'].append((element, count))
        else:
            categories['formatting'].append((element, count))
    
    # Sort each category by count
    for category in categories:
        categories[category].sort(key=lambda x: x[1], reverse=True)
    
    return categories

def main():
    """Run the comprehensive analysis"""
    base_path = "../osbooks-biology-bundle"
    
    print("=== CNXML Structure Analysis ===")
    print("Analyzing Biology 2e modules to understand parsing requirements...\n")
    
    # Analyze modules
    analysis = analyze_multiple_modules(base_path, num_modules=20)
    
    print(f"\n=== Analysis Results ===")
    print(f"Modules analyzed: {analysis['total_modules_analyzed']}")
    print(f"Unique elements found: {len(analysis['element_counts'])}")
    print(f"Total elements: {sum(analysis['element_counts'].values())}")
    
    # Categorize elements
    categories = categorize_elements(analysis['element_counts'])
    
    print("\n=== Element Categories ===")
    for category, elements in categories.items():
        if elements:
            print(f"\n{category.upper().replace('_', ' ')}:")
            for element, count in elements:
                print(f"  {element}: {count}")
    
    print("\n=== Section Types ===")
    for section_type, count in sorted(analysis['section_types'].items(), 
                                    key=lambda x: x[1], reverse=True):
        print(f"  {section_type}: {count}")
    
    # Show important attributes
    print("\n=== Important Attributes ===")
    important_elements = ['section', 'exercise', 'note', 'list', 'table', 'figure']
    for element in important_elements:
        # Clean element name
        clean_element = element.split('}')[-1] if '}' in element else element
        full_element = None
        for full_name in analysis['elements_with_attributes']:
            if full_name.endswith(clean_element):
                full_element = full_name
                break
        
        if full_element and full_element in analysis['elements_with_attributes']:
            attrs = analysis['elements_with_attributes'][full_element]
            if attrs:
                print(f"  {clean_element}:")
                for attr in sorted(attrs)[:10]:  # Show first 10
                    print(f"    {attr}")
    
    # Save detailed analysis
    output_file = Path("cnxml_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\nDetailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main()