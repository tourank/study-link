"""
Textbook Processor for StudyLink

This module processes the parsed CNXML data and provides a clean interface
for the API to access textbook content. It handles caching, content organization,
and preparation for RAG processing.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import pickle

from cnxml_parser import CNXMLParser, ModuleContent, TextbookStructure

class TextbookProcessor:
    """
    Processes and manages the Biology 2e textbook content.
    
    This class provides a high-level interface for accessing textbook content,
    handles caching for performance, and prepares content for RAG processing.
    """
    
    def __init__(self, base_path: str = "../osbooks-biology-bundle"):
        """
        Initialize the textbook processor.
        
        Args:
            base_path: Path to the textbook bundle directory
        """
        self.parser = CNXMLParser(base_path)
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache files
        self.structure_cache_file = self.cache_dir / "textbook_structure.pickle"
        self.modules_cache_file = self.cache_dir / "modules_cache.pickle"
        
        # In-memory caches
        self._structure_cache = None
        self._modules_cache = {}
        
        # Load cached data if available
        self._load_caches()
    
    def _load_caches(self):
        """Load cached data from disk to speed up subsequent runs"""
        try:
            if self.structure_cache_file.exists():
                with open(self.structure_cache_file, 'rb') as f:
                    self._structure_cache = pickle.load(f)
                print("Loaded textbook structure from cache")
            
            if self.modules_cache_file.exists():
                with open(self.modules_cache_file, 'rb') as f:
                    self._modules_cache = pickle.load(f)
                print(f"Loaded {len(self._modules_cache)} modules from cache")
        except Exception as e:
            print(f"Error loading caches: {e}")
            self._structure_cache = None
            self._modules_cache = {}
    
    def _save_caches(self):
        """Save cached data to disk"""
        try:
            if self._structure_cache:
                with open(self.structure_cache_file, 'wb') as f:
                    pickle.dump(self._structure_cache, f)
            
            if self._modules_cache:
                with open(self.modules_cache_file, 'wb') as f:
                    pickle.dump(self._modules_cache, f)
        except Exception as e:
            print(f"Error saving caches: {e}")
    
    def get_textbook_structure(self) -> Dict[str, Any]:
        """
        Get the hierarchical structure of the textbook.
        
        Returns:
            Dictionary containing the complete textbook structure
        """
        if self._structure_cache is None:
            print("Parsing textbook structure...")
            structure = self.parser.parse_collection_structure()
            
            # Convert to dictionary for JSON serialization
            self._structure_cache = {
                'title': structure.title,
                'chapters': structure.chapters
            }
            
            self._save_caches()
            print("Textbook structure parsed and cached")
        
        return self._structure_cache
    
    def get_module_content(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the content of a specific module.
        
        Args:
            module_id: The module ID (e.g., 'm66426')
            
        Returns:
            Dictionary containing module content and metadata
        """
        # Check cache first
        if module_id in self._modules_cache:
            return self._modules_cache[module_id]
        
        # Parse the module
        print(f"Parsing module {module_id}...")
        module_content = self.parser.parse_module(module_id)
        
        if module_content is None:
            return None
        
        # Convert to dictionary for JSON serialization
        module_dict = {
            'id': module_content.id,
            'title': module_content.title,
            'content': module_content.content,
            'figures': module_content.figures,
            'learning_objectives': module_content.learning_objectives,
            'key_terms': module_content.key_terms,
            'metadata': module_content.metadata
        }
        
        # Cache the result
        self._modules_cache[module_id] = module_dict
        self._save_caches()
        
        return module_dict
    
    def get_all_modules(self) -> List[Dict[str, Any]]:
        """
        Get all modules in the textbook.
        
        This method extracts all module IDs from the textbook structure
        and returns their content. Useful for bulk processing.
        
        Returns:
            List of all module dictionaries
        """
        structure = self.get_textbook_structure()
        all_modules = []
        
        def extract_module_ids(chapters):
            """Recursively extract module IDs from the structure"""
            module_ids = []
            for chapter in chapters:
                # Add modules directly in the chapter
                module_ids.extend(chapter.get('modules', []))
                
                # Add modules from sections
                for section in chapter.get('sections', []):
                    module_ids.extend(section.get('modules', []))
                    
                    # Handle nested sections if they exist
                    if 'sections' in section:
                        module_ids.extend(extract_module_ids([section]))
            
            return module_ids
        
        module_ids = extract_module_ids(structure['chapters'])
        
        # Get content for each module
        for module_id in module_ids:
            module_content = self.get_module_content(module_id)
            if module_content:
                all_modules.append(module_content)
        
        return all_modules
    
    def search_modules(self, query: str) -> List[Dict[str, Any]]:
        """
        Simple text search through module content.
        
        This is a basic implementation that will be replaced with
        vector similarity search in the RAG pipeline.
        
        Args:
            query: Search query string
            
        Returns:
            List of modules containing the query text
        """
        query_lower = query.lower()
        matching_modules = []
        
        structure = self.get_textbook_structure()
        
        def extract_module_ids(chapters):
            module_ids = []
            for chapter in chapters:
                module_ids.extend(chapter.get('modules', []))
                for section in chapter.get('sections', []):
                    module_ids.extend(section.get('modules', []))
            return module_ids
        
        module_ids = extract_module_ids(structure['chapters'])
        
        for module_id in module_ids:
            module_content = self.get_module_content(module_id)
            if module_content:
                # Search in title and content
                if (query_lower in module_content['title'].lower() or 
                    query_lower in module_content['content'].lower()):
                    matching_modules.append(module_content)
        
        return matching_modules
    
    def get_module_chunks(self, module_id: str, chunk_size: int = 500) -> List[Dict[str, Any]]:
        """
        Split a module's content into chunks for RAG processing.
        
        This prepares the content for embedding and vector storage.
        Each chunk includes metadata for proper attribution.
        
        Args:
            module_id: The module to chunk
            chunk_size: Target size for each chunk (in characters)
            
        Returns:
            List of content chunks with metadata
        """
        module_content = self.get_module_content(module_id)
        if not module_content:
            return []
        
        content = module_content['content']
        chunks = []
        
        # Simple chunking by paragraphs and sentences
        # This could be improved with more sophisticated chunking strategies
        sentences = content.split('. ')
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            # Add sentence to current chunk
            potential_chunk = current_chunk + sentence + ". "
            
            # If chunk is getting too long, finalize it
            if len(potential_chunk) > chunk_size and current_chunk:
                chunks.append({
                    'text': current_chunk.strip(),
                    'module_id': module_id,
                    'module_title': module_content['title'],
                    'chunk_index': chunk_index,
                    'metadata': module_content['metadata']
                })
                current_chunk = sentence + ". "
                chunk_index += 1
            else:
                current_chunk = potential_chunk
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'module_id': module_id,
                'module_title': module_content['title'],
                'chunk_index': chunk_index,
                'metadata': module_content['metadata']
            })
        
        return chunks
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the textbook content.
        
        Returns:
            Dictionary with content statistics
        """
        structure = self.get_textbook_structure()
        
        def count_modules(chapters):
            count = 0
            for chapter in chapters:
                count += len(chapter.get('modules', []))
                for section in chapter.get('sections', []):
                    count += len(section.get('modules', []))
            return count
        
        total_modules = count_modules(structure['chapters'])
        cached_modules = len(self._modules_cache)
        
        return {
            'total_chapters': len(structure['chapters']),
            'total_modules': total_modules,
            'cached_modules': cached_modules,
            'cache_hit_rate': cached_modules / total_modules if total_modules > 0 else 0
        }