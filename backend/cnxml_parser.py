"""
CNXML Parser for OpenStax Biology 2e Textbook

This module parses CNXML files from the OpenStax Biology textbook and converts
them into structured Python data that can be used for RAG processing.

CNXML is an XML format used by OpenStax that contains:
- Hierarchical document structure (chapters, sections, modules)
- Rich text content with formatting
- Figures, equations, and media references
- Educational metadata and learning objectives
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ModuleContent:
    """Represents a parsed module with all its content"""
    id: str
    title: str
    content: str  # Plain text content
    figures: List[Dict[str, Any]]
    learning_objectives: List[str]
    key_terms: List[str]
    metadata: Dict[str, Any]
    
@dataclass
class TextbookStructure:
    """Represents the hierarchical structure of the textbook"""
    title: str
    chapters: List[Dict[str, Any]]
    
class CNXMLParser:
    """
    Parser for CNXML files from OpenStax Biology 2e textbook.
    
    This class handles the conversion from CNXML format to structured Python data
    that can be easily processed for RAG applications.
    """
    
    def __init__(self, base_path: str = "../osbooks-biology-bundle"):
        """
        Initialize the parser with the path to the textbook bundle.
        
        Args:
            base_path: Path to the osbooks-biology-bundle directory
        """
        self.base_path = Path(base_path)
        self.modules_path = self.base_path / "modules"
        self.collection_path = self.base_path / "collections" / "biology-2e.collection.xml"
        
        # XML namespaces used in CNXML files
        self.namespaces = {
            'col': 'http://cnx.rice.edu/collxml',
            'md': 'http://cnx.rice.edu/mdml',
            'cnx': 'http://cnx.rice.edu/cnxml'
        }
    
    def parse_collection_structure(self) -> TextbookStructure:
        """
        Parse the collection XML file to understand the textbook structure.
        
        The collection file defines how modules are organized into chapters and sections.
        This gives us the hierarchical structure needed for navigation and references.
        
        Returns:
            TextbookStructure containing the full hierarchy
        """
        if not self.collection_path.exists():
            raise FileNotFoundError(f"Collection file not found: {self.collection_path}")
        
        tree = ET.parse(self.collection_path)
        root = tree.getroot()
        
        # Extract the main title
        title_elem = root.find('.//md:title', self.namespaces)
        title = title_elem.text if title_elem is not None else "Biology 2e"
        
        chapters = []
        
        # Parse the hierarchical structure
        # Find the main content element and get only direct subcollections (chapters)
        content_elem = root.find('col:content', self.namespaces)
        if content_elem is not None:
            for subcollection in content_elem.findall('col:subcollection', self.namespaces):
                chapter = self._parse_subcollection(subcollection)
                if chapter:
                    chapters.append(chapter)
        
        return TextbookStructure(title=title, chapters=chapters)
    
    def _parse_subcollection(self, subcollection_elem) -> Optional[Dict[str, Any]]:
        """
        Parse a subcollection element (chapter or section).
        
        Args:
            subcollection_elem: XML element representing a subcollection
            
        Returns:
            Dictionary containing the subcollection structure
        """
        title_elem = subcollection_elem.find('.//md:title', self.namespaces)
        if title_elem is None:
            return None
        
        title = title_elem.text
        
        # Look for nested subcollections (sections within chapters)
        sections = []
        modules = []
        
        content_elem = subcollection_elem.find('col:content', self.namespaces)
        if content_elem is not None:
            # Parse nested subcollections (sections)
            for nested_sub in content_elem.findall('col:subcollection', self.namespaces):
                section = self._parse_subcollection(nested_sub)
                if section:
                    sections.append(section)
            
            # Parse direct modules
            for module_elem in content_elem.findall('col:module', self.namespaces):
                module_id = module_elem.get('document')
                if module_id:
                    modules.append(module_id)
        
        return {
            'title': title,
            'sections': sections,
            'modules': modules
        }
    
    def parse_module(self, module_id: str) -> Optional[ModuleContent]:
        """
        Parse a single module file to extract its content.
        
        Args:
            module_id: The module ID (e.g., 'm66426')
            
        Returns:
            ModuleContent object with all parsed data
        """
        module_path = self.modules_path / module_id / "index.cnxml"
        
        if not module_path.exists():
            print(f"Warning: Module file not found: {module_path}")
            return None
        
        try:
            tree = ET.parse(module_path)
            root = tree.getroot()
            
            # Extract basic metadata
            metadata = self._extract_metadata(root)
            title = metadata.get('title', 'Untitled')
            
            # Also try to get title from the document title element
            title_elem = root.find('{http://cnx.rice.edu/cnxml}title')
            if title_elem is not None and title_elem.text:
                title = title_elem.text
                metadata['title'] = title
            
            # Extract the main content
            content_elem = root.find('{http://cnx.rice.edu/cnxml}content')
            if content_elem is None:
                # Try with namespace
                content_elem = root.find('.//content', self.namespaces)
            if content_elem is None:
                # Try without namespace
                content_elem = root.find('.//content')
            
            content_text = ""
            figures = []
            
            if content_elem is not None:
                content_text = self._extract_text_content(content_elem)
                figures = self._extract_figures(content_elem)
            
            # Extract learning objectives and key terms
            learning_objectives = self._extract_learning_objectives(root)
            key_terms = self._extract_key_terms(root)
            
            return ModuleContent(
                id=module_id,
                title=title,
                content=content_text,
                figures=figures,
                learning_objectives=learning_objectives,
                key_terms=key_terms,
                metadata=metadata
            )
            
        except ET.ParseError as e:
            print(f"Error parsing module {module_id}: {e}")
            return None
    
    def _extract_metadata(self, root) -> Dict[str, Any]:
        """Extract metadata from the module XML"""
        metadata = {}
        
        # Look for metadata element
        metadata_elem = root.find('{http://cnx.rice.edu/cnxml}metadata')
        if metadata_elem is not None:
            # Extract title
            title_elem = metadata_elem.find('.//{http://cnx.rice.edu/mdml}title')
            if title_elem is not None and title_elem.text:
                metadata['title'] = title_elem.text
            
            # Extract content ID
            content_id_elem = metadata_elem.find('.//{http://cnx.rice.edu/mdml}content-id')
            if content_id_elem is not None and content_id_elem.text:
                metadata['content_id'] = content_id_elem.text
            
            # Extract UUID
            uuid_elem = metadata_elem.find('.//{http://cnx.rice.edu/mdml}uuid')
            if uuid_elem is not None and uuid_elem.text:
                metadata['uuid'] = uuid_elem.text
        
        return metadata
    
    def _extract_text_content(self, element) -> str:
        """
        Extract plain text content from an XML element, removing markup.
        
        This recursively walks through the XML tree and extracts all text content,
        which is perfect for RAG processing where we need clean text.
        """
        text_parts = []
        
        # Get text from this element
        if element.text:
            text_parts.append(element.text.strip())
        
        # Recursively get text from child elements
        for child in element:
            child_text = self._extract_text_content(child)
            if child_text:
                text_parts.append(child_text)
            
            # Don't forget tail text (text after the closing tag)
            if child.tail:
                text_parts.append(child.tail.strip())
        
        return ' '.join(filter(None, text_parts))
    
    def _extract_figures(self, content_elem) -> List[Dict[str, Any]]:
        """Extract figure information from the content"""
        figures = []
        
        # Use the correct namespace for figure elements
        for figure_elem in content_elem.findall('.//{http://cnx.rice.edu/cnxml}figure'):
            figure_data = {
                'id': figure_elem.get('id', ''),
                'caption': '',
                'media_files': []
            }
            
            # Extract caption
            caption_elem = figure_elem.find('.//{http://cnx.rice.edu/cnxml}caption')
            if caption_elem is not None:
                figure_data['caption'] = self._extract_text_content(caption_elem)
            
            # Extract media files
            for media_elem in figure_elem.findall('.//{http://cnx.rice.edu/cnxml}media'):
                for image_elem in media_elem.findall('.//{http://cnx.rice.edu/cnxml}image'):
                    src = image_elem.get('src', '')
                    if src:
                        figure_data['media_files'].append({
                            'type': 'image',
                            'src': src,
                            'mime_type': image_elem.get('mime-type', ''),
                            'alt': media_elem.get('alt', '')
                        })
            
            figures.append(figure_data)
        
        return figures
    
    def _extract_learning_objectives(self, root) -> List[str]:
        """Extract learning objectives from the module"""
        objectives = []
        
        # Look for learning objectives in various possible locations
        for obj_elem in root.findall('.//para[@class="learning-objectives"]'):
            obj_text = self._extract_text_content(obj_elem)
            if obj_text:
                objectives.append(obj_text)
        
        return objectives
    
    def _extract_key_terms(self, root) -> List[str]:
        """Extract key terms from the module"""
        terms = []
        
        # Look for emphasized terms and glossary entries
        for term_elem in root.findall('.//term'):
            term_text = self._extract_text_content(term_elem)
            if term_text:
                terms.append(term_text)
        
        # Also look for emphasized text that might be key terms
        for emphasis_elem in root.findall('.//emphasis[@effect="bold"]'):
            term_text = self._extract_text_content(emphasis_elem)
            if term_text and len(term_text) < 50:  # Likely a term, not a sentence
                terms.append(term_text)
        
        # Look for terms with id attributes starting with "term-"
        for elem in root.findall('.//*[@id]'):
            if elem.get('id', '').startswith('term-'):
                term_text = self._extract_text_content(elem)
                if term_text and len(term_text) < 50:
                    terms.append(term_text)
        
        return list(set(terms))  # Remove duplicates