#!/usr/bin/env python3
"""
Comprehensive validation suite for the CNXML parser.

This script performs extensive testing to ensure the parser is working correctly
with very high confidence before moving to the next phase.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from comprehensive_cnxml_parser import ComprehensiveCNXMLParser

class ParserValidator:
    """Comprehensive validation suite for the CNXML parser"""
    
    def __init__(self, base_path="../osbooks-biology-bundle"):
        self.base_path = Path(base_path)
        self.parser = ComprehensiveCNXMLParser()
        self.validation_results = {
            'total_modules_tested': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'validation_errors': [],
            'content_statistics': {},
            'edge_cases_tested': 0,
            'performance_metrics': {}
        }
    
    def validate_known_content_counts(self):
        """Validate against manually verified content counts"""
        print("=== Validating Known Content Counts ===")
        
        # Manually verified counts for key modules
        known_counts = {
            'm66427': {  # The Science of Biology
                'learning_objectives': 4,
                'figures': 8,
                'exercises': 12,
                'sections': 9,
                'definitions': 27,
                'glossary_terms': 27
            },
            'm66428': {  # Themes and Concepts of Biology
                'learning_objectives': 4,
                'figures': 11,
                'exercises': 11,
                'sections': 9,
                'definitions': 25,
                'glossary_terms': 25
            },
            'm66430': {  # Atoms, Isotopes, Ions, and Molecules
                'learning_objectives': 4,
                'figures': 11,
                'exercises': 8,
                'sections': 14,
                'definitions': 44,
                'glossary_terms': 44
            }
        }
        
        validation_passed = True
        
        for module_id, expected in known_counts.items():
            print(f"\nValidating {module_id}:")
            module = self.parser.parse_module(module_id)
            
            if not module:
                print(f"  ✗ Failed to parse module {module_id}")
                validation_passed = False
                continue
            
            # Check each expected count
            actual_counts = {
                'learning_objectives': len(module.learning_objectives),
                'figures': len(module.all_figures),
                'exercises': len(module.all_exercises),
                'sections': len(module.sections),
                'definitions': len(module.definitions),
                'glossary_terms': len(module.glossary_terms)
            }
            
            for content_type, expected_count in expected.items():
                actual_count = actual_counts[content_type]
                if actual_count == expected_count:
                    print(f"  ✓ {content_type}: {actual_count} (matches expected)")
                else:
                    print(f"  ✗ {content_type}: {actual_count} (expected {expected_count})")
                    validation_passed = False
                    self.validation_results['validation_errors'].append(
                        f"{module_id}: {content_type} count mismatch - got {actual_count}, expected {expected_count}"
                    )
        
        return validation_passed
    
    def validate_content_quality(self):
        """Validate the quality and completeness of extracted content"""
        print("\n=== Validating Content Quality ===")
        
        test_modules = ['m66427', 'm66428', 'm66430']
        quality_checks_passed = True
        
        for module_id in test_modules:
            print(f"\nChecking content quality for {module_id}:")
            module = self.parser.parse_module(module_id)
            
            if not module:
                quality_checks_passed = False
                continue
            
            # Check 1: All figures should have captions
            figures_without_captions = [f for f in module.all_figures if not f.caption.strip()]
            if figures_without_captions:
                print(f"  ✗ {len(figures_without_captions)} figures without captions")
                quality_checks_passed = False
            else:
                print(f"  ✓ All {len(module.all_figures)} figures have captions")
            
            # Check 2: All exercises should have problems
            exercises_without_problems = [e for e in module.all_exercises if not e.problem.text.strip()]
            if exercises_without_problems:
                print(f"  ✗ {len(exercises_without_problems)} exercises without problems")
                quality_checks_passed = False
            else:
                print(f"  ✓ All {len(module.all_exercises)} exercises have problems")
            
            # Check 3: All definitions should have terms and meanings
            incomplete_definitions = [d for d in module.definitions if not d.term.strip() or not d.meaning.strip()]
            if incomplete_definitions:
                print(f"  ✗ {len(incomplete_definitions)} incomplete definitions")
                quality_checks_passed = False
            else:
                print(f"  ✓ All {len(module.definitions)} definitions are complete")
            
            # Check 4: Sections should have proper hierarchy
            sections_without_titles = [s for s in module.sections if not s.title.strip()]
            if sections_without_titles:
                print(f"  ✗ {len(sections_without_titles)} sections without titles")
                quality_checks_passed = False
            else:
                print(f"  ✓ All {len(module.sections)} sections have titles")
            
            # Check 5: Flattened content should be substantial
            min_expected_content_length = 10000  # At least 10KB of text
            if len(module.all_text) < min_expected_content_length:
                print(f"  ✗ Flattened content too short: {len(module.all_text)} chars")
                quality_checks_passed = False
            else:
                print(f"  ✓ Flattened content length: {len(module.all_text)} chars")
        
        return quality_checks_passed
    
    def validate_xml_structure_handling(self):
        """Validate that the parser handles XML structure correctly"""
        print("\n=== Validating XML Structure Handling ===")
        
        structure_tests_passed = True
        
        # Test module with complex nested structure
        module = self.parser.parse_module('m66427')
        if not module:
            return False
        
        # Check 1: Nested sections are properly extracted
        sections_with_subsections = [s for s in module.sections if s.subsections]
        if not sections_with_subsections:
            print("  ✗ No nested sections found (expected some)")
            structure_tests_passed = False
        else:
            total_subsections = sum(len(s.subsections) for s in sections_with_subsections)
            print(f"  ✓ Found {len(sections_with_subsections)} sections with {total_subsections} subsections")
        
        # Check 2: Content is not duplicated between parent and child sections
        all_figure_ids = [f.id for f in module.all_figures]
        if len(all_figure_ids) != len(set(all_figure_ids)):
            print("  ✗ Duplicate figures found in aggregated list")
            structure_tests_passed = False
        else:
            print(f"  ✓ No duplicate figures in aggregated list")
        
        # Check 3: Different section types are properly identified
        section_types = {s.section_type for s in module.sections}
        expected_types = {'regular', 'summary', 'multiple-choice', 'critical-thinking', 'visual-exercise'}
        if not expected_types.issubset(section_types):
            print(f"  ✗ Missing expected section types. Found: {section_types}")
            structure_tests_passed = False
        else:
            print(f"  ✓ All expected section types found: {section_types}")
        
        return structure_tests_passed
    
    def validate_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n=== Validating Edge Cases ===")
        
        edge_case_tests_passed = True
        
        # Test 1: Non-existent module
        non_existent = self.parser.parse_module('m99999')
        if non_existent is not None:
            print("  ✗ Non-existent module should return None")
            edge_case_tests_passed = False
        else:
            print("  ✓ Non-existent module returns None")
        
        # Test 2: Module with minimal content
        # Find a module with fewer elements to test minimal content handling
        minimal_modules = ['m66436']  # Carbon module (smaller)
        for module_id in minimal_modules:
            module = self.parser.parse_module(module_id)
            if module:
                print(f"  ✓ Successfully parsed minimal module {module_id}")
                print(f"    - Sections: {len(module.sections)}")
                print(f"    - Figures: {len(module.all_figures)}")
                print(f"    - Exercises: {len(module.all_exercises)}")
            else:
                print(f"  ✗ Failed to parse minimal module {module_id}")
                edge_case_tests_passed = False
        
        self.validation_results['edge_cases_tested'] = 2
        return edge_case_tests_passed
    
    def validate_performance(self):
        """Test parser performance on multiple modules"""
        print("\n=== Validating Performance ===")
        
        import time
        
        # Test modules (actual biology modules from different ranges)
        test_modules = [
            'm66427', 'm66428', 'm66429', 'm66430', 'm66436',  # Known working modules
            'm45417', 'm45445', 'm45476', 'm45515', 'm45540',  # Earlier modules
            'm62733', 'm62784', 'm62805', 'm62833', 'm62862'   # Middle range modules
        ]
        
        successful_parses = 0
        total_parse_time = 0
        
        for module_id in test_modules:
            start_time = time.time()
            module = self.parser.parse_module(module_id)
            parse_time = time.time() - start_time
            
            if module:
                successful_parses += 1
                print(f"  ✓ {module_id}: {parse_time:.3f}s - {len(module.all_text)} chars")
            else:
                print(f"  ✗ {module_id}: Failed to parse")
            
            total_parse_time += parse_time
        
        avg_parse_time = total_parse_time / len(test_modules)
        success_rate = successful_parses / len(test_modules)
        
        print(f"\nPerformance Summary:")
        print(f"  Success rate: {success_rate:.1%} ({successful_parses}/{len(test_modules)})")
        print(f"  Average parse time: {avg_parse_time:.3f}s")
        print(f"  Total parse time: {total_parse_time:.3f}s")
        
        self.validation_results['performance_metrics'] = {
            'modules_tested': len(test_modules),
            'successful_parses': successful_parses,
            'success_rate': success_rate,
            'avg_parse_time_seconds': avg_parse_time,
            'total_parse_time_seconds': total_parse_time
        }
        
        # Performance should be reasonable (< 1 second per module on average)
        return avg_parse_time < 1.0 and success_rate > 0.8
    
    def validate_content_consistency(self):
        """Validate that content extraction is consistent across similar modules"""
        print("\n=== Validating Content Consistency ===")
        
        # Test multiple modules to ensure consistent structure
        test_modules = ['m66427', 'm66428', 'm66430']
        consistency_passed = True
        
        modules_data = []
        for module_id in test_modules:
            module = self.parser.parse_module(module_id)
            if module:
                modules_data.append({
                    'id': module_id,
                    'title': module.title,
                    'section_count': len(module.sections),
                    'has_learning_objectives': len(module.learning_objectives) > 0,
                    'has_figures': len(module.all_figures) > 0,
                    'has_exercises': len(module.all_exercises) > 0,
                    'has_definitions': len(module.definitions) > 0,
                    'has_glossary': len(module.glossary_terms) > 0,
                    'has_flattened_content': len(module.all_text) > 0
                })
        
        print(f"Analyzed {len(modules_data)} modules for consistency:")
        
        # Check that all modules have expected content types
        for module_data in modules_data:
            module_id = module_data['id']
            checks = [
                ('learning_objectives', module_data['has_learning_objectives']),
                ('figures', module_data['has_figures']),
                ('exercises', module_data['has_exercises']),
                ('definitions', module_data['has_definitions']),
                ('glossary', module_data['has_glossary']),
                ('flattened_content', module_data['has_flattened_content'])
            ]
            
            failed_checks = [name for name, passed in checks if not passed]
            if failed_checks:
                print(f"  ✗ {module_id}: Missing {', '.join(failed_checks)}")
                consistency_passed = False
            else:
                print(f"  ✓ {module_id}: All content types present")
        
        return consistency_passed
    
    def run_comprehensive_validation(self):
        """Run all validation tests"""
        print("🔍 COMPREHENSIVE PARSER VALIDATION")
        print("=" * 50)
        
        validation_tests = [
            ("Known Content Counts", self.validate_known_content_counts),
            ("Content Quality", self.validate_content_quality),
            ("XML Structure Handling", self.validate_xml_structure_handling),
            ("Edge Cases", self.validate_edge_cases),
            ("Performance", self.validate_performance),
            ("Content Consistency", self.validate_content_consistency)
        ]
        
        all_tests_passed = True
        test_results = {}
        
        for test_name, test_func in validation_tests:
            print(f"\n{test_name}:")
            print("-" * 30)
            
            try:
                test_passed = test_func()
                test_results[test_name] = test_passed
                
                if test_passed:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
                    all_tests_passed = False
                    
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                test_results[test_name] = False
                all_tests_passed = False
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print(f"Success rate: {passed_tests/total_tests:.1%}")
        
        if all_tests_passed:
            print("\n🎉 ALL VALIDATION TESTS PASSED!")
            print("✅ Parser is ready for production use")
        else:
            print("\n⚠️  SOME VALIDATION TESTS FAILED")
            print("❌ Parser needs fixes before production use")
            
            if self.validation_results['validation_errors']:
                print("\nValidation Errors:")
                for error in self.validation_results['validation_errors']:
                    print(f"  - {error}")
        
        # Save detailed results
        self.validation_results['test_results'] = test_results
        self.validation_results['overall_success'] = all_tests_passed
        
        with open('parser_validation_results.json', 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: parser_validation_results.json")
        
        return all_tests_passed

def main():
    """Run the comprehensive validation suite"""
    validator = ParserValidator()
    success = validator.run_comprehensive_validation()
    
    if success:
        print("\n🚀 Parser validation completed successfully!")
        print("Ready to proceed to the next development phase.")
    else:
        print("\n🔧 Parser validation found issues that need to be addressed.")
        print("Please review the validation results and fix any problems.")
    
    return success

if __name__ == "__main__":
    main()