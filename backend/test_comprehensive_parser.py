#!/usr/bin/env python3
"""
Test script for the comprehensive CNXML parser.

This script tests all the educational content extraction capabilities.
"""

from comprehensive_cnxml_parser import ComprehensiveCNXMLParser
import json

def test_parser_comprehensive():
    """Test the comprehensive parser with detailed output"""
    print("=== Testing Comprehensive CNXML Parser ===")
    
    parser = ComprehensiveCNXMLParser()
    
    # Test with a content-rich module - focus on m66427 for detailed debugging
    test_modules = ['m66427', 'm66428', 'm66430', 'm66436']  # Science of Biology, Themes, Chemical Foundation
    
    for module_id in test_modules:
        print(f"\n--- Testing Module: {module_id} ---")
        
        module = parser.parse_module(module_id)
        
        if module is None:
            print(f"✗ Failed to parse module {module_id}")
            continue
        
        print(f"✓ Module: {module.title}")
        print(f"  ID: {module.id}")
        print(f"  Metadata: {module.metadata}")
        
        # Test learning objectives
        print(f"  Learning objectives: {len(module.learning_objectives)}")
        for i, obj in enumerate(module.learning_objectives):
            print(f"    {i+1}. {obj}")
        
        # Test sections - show more detail for m66427
        print(f"  Sections: {len(module.sections)}")
        section_limit = len(module.sections) if module_id == 'm66427' else 3
        for i, section in enumerate(module.sections[:section_limit]):
            print(f"    Section {i+1}: {section.title} (type: {section.section_type})")
            print(f"      Content: {len(section.content)} paragraphs")
            print(f"      Figures: {len(section.figures)}")
            print(f"      Tables: {len(section.tables)}")
            print(f"      Lists: {len(section.lists)}")
            print(f"      Notes: {len(section.notes)}")
            print(f"      Exercises: {len(section.exercises)}")
            print(f"      Subsections: {len(section.subsections)}")
            
            # Show subsection details for m66427
            if module_id == 'm66427':
                for j, subsection in enumerate(section.subsections):
                    print(f"        Subsection {j+1}: {subsection.title} (type: {subsection.section_type})")
                    print(f"          Content: {len(subsection.content)} paragraphs")
                    print(f"          Figures: {len(subsection.figures)}")
                    print(f"          Tables: {len(subsection.tables)}")
                    print(f"          Lists: {len(subsection.lists)}")
                    print(f"          Notes: {len(subsection.notes)}")
                    print(f"          Exercises: {len(subsection.exercises)}")
        
        # Test figures - show all for m66427
        print(f"  All figures: {len(module.all_figures)}")
        figure_limit = len(module.all_figures) if module_id == 'm66427' else 3
        for i, figure in enumerate(module.all_figures[:figure_limit]):
            print(f"    Figure {i+1}: {figure.id} (class: {figure.class_type})")
            print(f"      Caption: {figure.caption[:100]}...")
            print(f"      Media files: {len(figure.media_files)}")
            if figure.media_files:
                print(f"      Media: {figure.media_files[0]['src']}")
        
        # Test exercises - show more for m66427
        print(f"  All exercises: {len(module.all_exercises)}")
        exercise_limit = len(module.all_exercises) if module_id == 'm66427' else 3
        for i, exercise in enumerate(module.all_exercises[:exercise_limit]):
            print(f"    Exercise {i+1}: {exercise.id}")
            print(f"      Problem: {exercise.problem.text[:100]}...")
            print(f"      Has solution: {exercise.solution is not None}")
            print(f"      Has commentary: {exercise.commentary is not None}")
        
        # Test definitions (showing first 3 for brevity)
        print(f"  Definitions: {len(module.definitions)}")
        for i, definition in enumerate(module.definitions[:3]):
            print(f"    Definition {i+1}: {definition.term}")
            print(f"      Meaning: {definition.meaning[:100]}...")
        
        # Test glossary (showing first 3 for brevity)
        print(f"  Glossary terms: {len(module.glossary_terms)}")
        for i, term in enumerate(module.glossary_terms[:3]):
            print(f"    Term {i+1}: {term.term}")
            print(f"      Meaning: {term.meaning[:100]}...")
        
        # Test flattened content
        print(f"  Flattened content length: {len(module.all_text)} characters")
        print(f"  Content preview: {module.all_text[:200]}...")
        
        print()

def test_specific_content_types():
    """Test specific content types in detail"""
    print("=== Testing Specific Content Types ===")
    
    parser = ComprehensiveCNXMLParser()
    
    # Test with a module known to have exercises
    module = parser.parse_module('m66427')
    if module is None:
        print("✗ Failed to parse test module")
        return
    
    print(f"Module: {module.title}")
    
    # Test text content with formatting
    print(f"\n--- Text Content Analysis ---")
    total_paragraphs = 0
    total_emphasis = 0
    total_terms = 0
    total_links = 0
    
    for section in module.sections:
        for para in section.content:
            total_paragraphs += 1
            total_emphasis += len(para.emphasis)
            total_terms += len(para.terms)
            total_links += len(para.links)
    
    print(f"Total paragraphs: {total_paragraphs}")
    print(f"Total emphasis elements: {total_emphasis}")
    print(f"Total terms in text: {total_terms}")
    print(f"Total links: {total_links}")
    
    # Show sample formatted content
    if module.sections and module.sections[0].content:
        sample_para = module.sections[0].content[0]
        print(f"\nSample paragraph:")
        print(f"  Text: {sample_para.text[:200]}...")
        print(f"  Emphasis: {sample_para.emphasis[:3]}")
        print(f"  Terms: {sample_para.terms[:3]}")
        print(f"  Links: {sample_para.links[:3]}")
    
    # Test section types
    print(f"\n--- Section Types ---")
    section_types = {}
    for section in module.sections:
        section_types[section.section_type] = section_types.get(section.section_type, 0) + 1
    
    for section_type, count in section_types.items():
        print(f"  {section_type}: {count}")

def test_educational_structure():
    """Test educational structure parsing"""
    print("=== Testing Educational Structure ===")
    
    parser = ComprehensiveCNXMLParser()
    
    # Test multiple modules for comprehensive coverage
    test_modules = ['m66427', 'm66428', 'm66430', 'm66437']
    
    total_stats = {
        'modules': 0,
        'sections': 0,
        'paragraphs': 0,
        'figures': 0,
        'tables': 0,
        'lists': 0,
        'notes': 0,
        'exercises': 0,
        'definitions': 0,
        'glossary_terms': 0
    }
    
    for module_id in test_modules:
        module = parser.parse_module(module_id)
        if module:
            total_stats['modules'] += 1
            total_stats['sections'] += len(module.sections)
            total_stats['figures'] += len(module.all_figures)
            total_stats['exercises'] += len(module.all_exercises)
            total_stats['definitions'] += len(module.definitions)
            total_stats['glossary_terms'] += len(module.glossary_terms)
            
            # Count content in sections
            for section in module.sections:
                total_stats['paragraphs'] += len(section.content)
                total_stats['tables'] += len(section.tables)
                total_stats['lists'] += len(section.lists)
                total_stats['notes'] += len(section.notes)
    
    print(f"Analysis of {total_stats['modules']} modules:")
    for key, value in total_stats.items():
        if key != 'modules':
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # Calculate averages
    if total_stats['modules'] > 0:
        print(f"\nAverages per module:")
        for key, value in total_stats.items():
            if key != 'modules':
                avg = value / total_stats['modules']
                print(f"  {key.replace('_', ' ').title()}: {avg:.1f}")

def debug_m66427_detailed():
    """Detailed debugging output for m66427"""
    print("=== Detailed Debug: m66427 ===")
    
    parser = ComprehensiveCNXMLParser()
    module = parser.parse_module('m66427')
    
    if not module:
        print("✗ Failed to parse m66427")
        return
    
    print(f"Module: {module.title}")
    print(f"ID: {module.id}")
    print(f"Metadata: {module.metadata}")
    
    # Count all content types
    total_content = {
        'paragraphs': 0,
        'figures': 0,
        'tables': 0,
        'lists': 0,
        'notes': 0,
        'exercises': 0
    }
    
    print(f"\n=== Complete Section Breakdown ===")
    for i, section in enumerate(module.sections):
        print(f"\nSection {i+1}: \"{section.title}\" (ID: {section.id}, Type: {section.section_type})")
        print(f"  Content: {len(section.content)} paragraphs")
        print(f"  Figures: {len(section.figures)} - {[f.id for f in section.figures]}")
        print(f"  Tables: {len(section.tables)} - {[t.id for t in section.tables]}")
        print(f"  Lists: {len(section.lists)} - {[l.id for l in section.lists]}")
        print(f"  Notes: {len(section.notes)} - {[n.id for n in section.notes]}")
        print(f"  Exercises: {len(section.exercises)} - {[e.id for e in section.exercises]}")
        
        # Update totals
        total_content['paragraphs'] += len(section.content)
        total_content['figures'] += len(section.figures)
        total_content['tables'] += len(section.tables)
        total_content['lists'] += len(section.lists)
        total_content['notes'] += len(section.notes)
        total_content['exercises'] += len(section.exercises)
        
        # Show subsections with full detail
        for j, subsection in enumerate(section.subsections):
            print(f"    Subsection {j+1}: \"{subsection.title}\" (ID: {subsection.id}, Type: {subsection.section_type})")
            print(f"      Content: {len(subsection.content)} paragraphs")
            print(f"      Figures: {len(subsection.figures)} - {[f.id for f in subsection.figures]}")
            print(f"      Tables: {len(subsection.tables)} - {[t.id for t in subsection.tables]}")
            print(f"      Lists: {len(subsection.lists)} - {[l.id for l in subsection.lists]}")
            print(f"      Notes: {len(subsection.notes)} - {[n.id for n in subsection.notes]}")
            print(f"      Exercises: {len(subsection.exercises)} - {[e.id for e in subsection.exercises]}")
            
            # Update totals
            total_content['paragraphs'] += len(subsection.content)
            total_content['figures'] += len(subsection.figures)
            total_content['tables'] += len(subsection.tables)
            total_content['lists'] += len(subsection.lists)
            total_content['notes'] += len(subsection.notes)
            total_content['exercises'] += len(subsection.exercises)
    
    print(f"\n=== Content Totals ===")
    for content_type, count in total_content.items():
        print(f"{content_type.title()}: {count}")
    
    print(f"\n=== Aggregated Lists ===")
    print(f"All figures: {len(module.all_figures)} - {[f.id for f in module.all_figures]}")
    print(f"All exercises: {len(module.all_exercises)} - {[e.id for e in module.all_exercises]}")
    print(f"All definitions: {len(module.all_definitions)} - {[d.term for d in module.all_definitions[:5]]}...")
    
    print(f"\n=== Sample Content Details ===")
    
    # Show first few figures with full details
    print(f"\nFigures ({len(module.all_figures)} total):")
    for i, figure in enumerate(module.all_figures[:5]):
        print(f"  {i+1}. {figure.id} (class: '{figure.class_type}')")
        print(f"     Caption: {figure.caption[:150]}...")
        print(f"     Media: {len(figure.media_files)} files")
        for media in figure.media_files:
            print(f"       - {media['type']}: {media['src']}")
    
    # Show first few exercises with full details
    print(f"\nExercises ({len(module.all_exercises)} total):")
    for i, exercise in enumerate(module.all_exercises[:5]):
        print(f"  {i+1}. {exercise.id}")
        print(f"     Problem: {exercise.problem.text[:100]}...")
        if exercise.solution:
            print(f"     Solution: {exercise.solution.text[:100]}...")
        if exercise.commentary:
            print(f"     Commentary: {exercise.commentary.text[:100]}...")
    
    # Show lists with details
    print(f"\nLists (found in sections):")
    list_count = 0
    for section in module.sections:
        for list_item in section.lists:
            list_count += 1
            print(f"  {list_count}. {list_item.id} in section '{section.title}'")
            print(f"     Type: {list_item.list_type}, Style: {list_item.number_style}")
            print(f"     Items: {len(list_item.items)}")
            for j, item in enumerate(list_item.items[:3]):
                print(f"       {j+1}. {item.text[:80]}...")
        
        for subsection in section.subsections:
            for list_item in subsection.lists:
                list_count += 1
                print(f"  {list_count}. {list_item.id} in subsection '{subsection.title}'")
                print(f"     Type: {list_item.list_type}, Style: {list_item.number_style}")
                print(f"     Items: {len(list_item.items)}")
                for j, item in enumerate(list_item.items[:3]):
                    print(f"       {j+1}. {item.text[:80]}...")
    
    # Show tables with details
    print(f"\nTables (found in sections):")
    table_count = 0
    for section in module.sections:
        for table in section.tables:
            table_count += 1
            print(f"  {table_count}. {table.id} in section '{section.title}'")
            print(f"     Title: {table.title}")
            print(f"     Summary: {table.summary}")
            print(f"     Headers: {table.headers}")
            print(f"     Rows: {len(table.rows)}")
            if table.rows:
                print(f"     Sample row: {table.rows[0]}")
        
        for subsection in section.subsections:
            for table in subsection.tables:
                table_count += 1
                print(f"  {table_count}. {table.id} in subsection '{subsection.title}'")
                print(f"     Title: {table.title}")
                print(f"     Summary: {table.summary}")
                print(f"     Headers: {table.headers}")
                print(f"     Rows: {len(table.rows)}")
                if table.rows:
                    print(f"     Sample row: {table.rows[0]}")
    
    print(f"\n=== Learning Objectives ===")
    for i, obj in enumerate(module.learning_objectives):
        print(f"  {i+1}. {obj}")
    
    print(f"\n=== Flattened Content Stats ===")
    print(f"Total flattened text: {len(module.all_text)} characters")
    print(f"Lines in flattened text: {len(module.all_text.split('\\n'))}")
    print(f"First 300 chars: {module.all_text[:300]}...")

def save_sample_output():
    """Save sample parsed output for inspection"""
    print("=== Saving Sample Output ===")
    
    parser = ComprehensiveCNXMLParser()
    module = parser.parse_module('m66427')
    
    if module:
        # Convert to dict for JSON serialization
        sample_data = {
            'id': module.id,
            'title': module.title,
            'metadata': module.metadata,
            'learning_objectives': module.learning_objectives,
            'section_count': len(module.sections),
            'figure_count': len(module.all_figures),
            'exercise_count': len(module.all_exercises),
            'definition_count': len(module.definitions),
            'glossary_count': len(module.glossary_terms),
            'flattened_content_length': len(module.all_text),
            'sample_section': {
                'title': module.sections[0].title if module.sections else None,
                'content_paragraphs': len(module.sections[0].content) if module.sections else 0,
                'section_type': module.sections[0].section_type if module.sections else None
            } if module.sections else None,
            'sample_figure': {
                'id': module.all_figures[0].id,
                'caption': module.all_figures[0].caption[:200],
                'media_count': len(module.all_figures[0].media_files)
            } if module.all_figures else None,
            'sample_exercise': {
                'id': module.all_exercises[0].id,
                'problem': module.all_exercises[0].problem.text[:200],
                'has_solution': module.all_exercises[0].solution is not None
            } if module.all_exercises else None
        }
        
        with open('sample_parsed_output.json', 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        print("✓ Sample output saved to sample_parsed_output.json")
        
        # Also save flattened content sample
        with open('sample_flattened_content.txt', 'w') as f:
            f.write(module.all_text[:5000])  # First 5000 characters
        
        print("✓ Flattened content sample saved to sample_flattened_content.txt")

if __name__ == "__main__":
    test_parser_comprehensive()
    test_specific_content_types()
    test_educational_structure()
    save_sample_output()
