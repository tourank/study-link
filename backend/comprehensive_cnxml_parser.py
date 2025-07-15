"""
Comprehensive CNXML Parser for OpenStax Biology 2e

This parser extracts all educational content from CNXML modules including:
- Basic content (paragraphs, emphasis, titles)
- Educational structure (sections, lists, tables, notes)
- Exercises and assessments (problems, solutions, commentary)
- Definitions and glossary terms
- Media and figures
- Navigation links and cross-references
- Metadata

The parser produces structured, clean data suitable for RAG processing while
preserving the educational structure and relationships.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

# Define data structures for different content types

@dataclass
class TextContent:
    """Represents formatted text content"""
    text: str
    emphasis: List[str] = field(default_factory=list)  # italics, bold, etc.
    terms: List[str] = field(default_factory=list)     # key terms in this text
    links: List[Dict[str, str]] = field(default_factory=list)  # cross-references

@dataclass
class Figure:
    """Represents a figure with media and caption"""
    id: str
    caption: str
    media_files: List[Dict[str, Any]]
    class_type: str = ""  # e.g., "splash" for chapter openers

@dataclass
class Table:
    """Represents a data table"""
    id: str
    title: str
    summary: str
    headers: List[str]
    rows: List[List[str]]
    class_type: str = ""

@dataclass
class ListItem:
    """Represents a list (bulleted, numbered, etc.)"""
    id: str
    list_type: str  # "bulleted", "enumerated", etc.
    items: List[TextContent]
    number_style: str = "decimal"  # "lower-alpha", "upper-roman", etc.

@dataclass
class Definition:
    """Represents a term definition"""
    id: str
    term: str
    meaning: str
    context: str = ""  # surrounding context

@dataclass
class Exercise:
    """Represents an exercise with problem and solution"""
    id: str
    problem: TextContent
    solution: Optional[TextContent] = None
    commentary: Optional[TextContent] = None
    exercise_type: str = "general"  # "multiple-choice", "critical-thinking", etc.

@dataclass
class Note:
    """Represents special notes/callouts"""
    id: str
    content: TextContent
    note_type: str = "general"  # "career", "everyday", "evolution", etc.

@dataclass
class Section:
    """Represents a section with all its content"""
    id: str
    title: str
    content: List[TextContent]
    figures: List[Figure]
    tables: List[Table]
    lists: List[ListItem]
    notes: List[Note]
    exercises: List[Exercise]
    subsections: List['Section']  # nested sections
    section_type: str = "regular"  # "summary", "multiple-choice", etc.

@dataclass
class Module:
    """Represents a complete module with all educational content"""
    id: str
    title: str
    metadata: Dict[str, Any]
    
    # Content organization
    sections: List[Section]
    
    # Educational elements
    definitions: List[Definition]
    glossary_terms: List[Definition]
    
    # Learning objectives (from abstract)
    learning_objectives: List[str]
    
    # All content flattened for RAG
    all_text: str = ""
    all_figures: List[Figure] = field(default_factory=list)
    all_exercises: List[Exercise] = field(default_factory=list)
    all_definitions: List[Definition] = field(default_factory=list)

class CNXMLNamespace:
    """Handles CNXML namespace constants"""
    CNXML = "http://cnx.rice.edu/cnxml"
    MDML = "http://cnx.rice.edu/mdml"
    MATHML = "http://www.w3.org/1998/Math/MathML"
    
    @classmethod
    def tag(cls, namespace: str, element: str) -> str:
        """Create a namespaced tag"""
        return f"{{{namespace}}}{element}"

class ComprehensiveCNXMLParser:
    """
    Comprehensive parser for CNXML biology modules.
    
    This parser extracts all educational content while preserving structure
    and relationships between elements.
    """
    
    def __init__(self, base_path: str = "../osbooks-biology-bundle"):
        self.base_path = Path(base_path)
        self.modules_path = self.base_path / "modules"
        self.collection_path = self.base_path / "collections" / "biology-2e.collection.xml"
        
        # Create namespace shortcuts
        self.ns = CNXMLNamespace()
        
    def parse_module(self, module_id: str) -> Optional[Module]:
        """
        Parse a complete module with all educational content.
        
        Args:
            module_id: The module ID (e.g., 'm66427')
            
        Returns:
            Module object with all parsed content
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
            title = self._extract_title(root)
            
            # Extract learning objectives from abstract
            learning_objectives = self._extract_learning_objectives(root)
            
            # Parse the main content
            content_elem = root.find(self.ns.tag(self.ns.CNXML, 'content'))
            if content_elem is None:
                print(f"Warning: No content element found in {module_id}")
                return None
            
            # Parse all sections
            sections = self._parse_sections(content_elem)
            
            # Extract definitions and glossary
            definitions = self._extract_definitions(root)
            glossary_terms = self._extract_glossary(root)
            
            # Create the module
            module = Module(
                id=module_id,
                title=title,
                metadata=metadata,
                sections=sections,
                definitions=definitions,
                glossary_terms=glossary_terms,
                learning_objectives=learning_objectives
            )
            
            # Flatten content for RAG
            self._flatten_content(module)
            
            return module
            
        except ET.ParseError as e:
            print(f"Error parsing module {module_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error parsing module {module_id}: {e}")
            return None
    
    def _extract_metadata(self, root) -> Dict[str, Any]:
        """Extract metadata from the module"""
        metadata = {}
        
        metadata_elem = root.find(self.ns.tag(self.ns.CNXML, 'metadata'))
        if metadata_elem is not None:
            # Extract various metadata fields
            for field in ['title', 'content-id', 'uuid']:
                elem = metadata_elem.find(f'.//{self.ns.tag(self.ns.MDML, field)}')
                if elem is not None and elem.text:
                    metadata[field.replace('-', '_')] = elem.text
        
        return metadata
    
    def _extract_title(self, root) -> str:
        """Extract the module title"""
        # Try document title first
        title_elem = root.find(self.ns.tag(self.ns.CNXML, 'title'))
        if title_elem is not None and title_elem.text:
            return title_elem.text
        
        # Fall back to metadata title
        metadata_elem = root.find(self.ns.tag(self.ns.CNXML, 'metadata'))
        if metadata_elem is not None:
            title_elem = metadata_elem.find(f'.//{self.ns.tag(self.ns.MDML, "title")}')
            if title_elem is not None and title_elem.text:
                return title_elem.text
        
        return "Untitled"
    
    def _extract_learning_objectives(self, root) -> List[str]:
        """Extract learning objectives from the abstract"""
        objectives = []
        
        # Look in metadata abstract
        metadata_elem = root.find(self.ns.tag(self.ns.CNXML, 'metadata'))
        if metadata_elem is not None:
            abstract_elem = metadata_elem.find(f'.//{self.ns.tag(self.ns.MDML, "abstract")}')
            if abstract_elem is not None:
                # Extract list items from abstract
                for item in abstract_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "item")}'):
                    obj_text = self._extract_text_content(item)
                    if obj_text:
                        objectives.append(obj_text)
        
        return objectives
    
    def _parse_sections(self, content_elem) -> List[Section]:
        """Parse all sections in the content"""
        sections = []
        
        # Direct content (not in sections)
        direct_content = self._extract_direct_content(content_elem)
        if direct_content:
            # Create a main section for direct content
            main_section = Section(
                id="main",
                title="Main Content",
                content=direct_content['paragraphs'],
                figures=direct_content['figures'],
                tables=direct_content['tables'],
                lists=direct_content['lists'],
                notes=direct_content['notes'],
                exercises=direct_content['exercises'],
                subsections=[]
            )
            sections.append(main_section)
        
        # Parse only direct child sections (not nested ones)
        for section_elem in content_elem.findall(f'./{self.ns.tag(self.ns.CNXML, "section")}'):
            section = self._parse_section(section_elem)
            if section:
                sections.append(section)
        
        return sections
    
    def _parse_section(self, section_elem) -> Optional[Section]:
        """Parse a single section element"""
        section_id = section_elem.get('id', '')
        section_type = section_elem.get('class', 'regular')
        
        # Extract title
        title_elem = section_elem.find(self.ns.tag(self.ns.CNXML, 'title'))
        title = title_elem.text if title_elem is not None else "Untitled Section"
        
        # Extract content
        content_data = self._extract_direct_content(section_elem)
        
        # Parse direct child subsections only
        subsections = []
        for subsection_elem in section_elem.findall(f'./{self.ns.tag(self.ns.CNXML, "section")}'):
            subsection = self._parse_section(subsection_elem)
            if subsection:
                subsections.append(subsection)
        
        return Section(
            id=section_id,
            title=title,
            content=content_data['paragraphs'],
            figures=content_data['figures'],
            tables=content_data['tables'],
            lists=content_data['lists'],
            notes=content_data['notes'],
            exercises=content_data['exercises'],
            subsections=subsections,
            section_type=section_type
        )
    
    def _extract_direct_content(self, parent_elem) -> Dict[str, List]:
        """Extract all direct content from an element"""
        content = {
            'paragraphs': [],
            'figures': [],
            'tables': [],
            'lists': [],
            'notes': [],
            'exercises': []
        }
        
        # Extract paragraphs
        for para_elem in parent_elem.findall(f'./{self.ns.tag(self.ns.CNXML, "para")}'):
            text_content = self._parse_text_content(para_elem)
            if text_content.text.strip():
                content['paragraphs'].append(text_content)
        
        # Extract figures (including nested ones in notes, etc.)
        # But exclude figures that are in child sections
        child_sections = parent_elem.findall(f'./{self.ns.tag(self.ns.CNXML, "section")}')
        child_section_figures = set()
        for child_section in child_sections:
            for fig in child_section.findall(f'.//{self.ns.tag(self.ns.CNXML, "figure")}'):
                child_section_figures.add(fig)
        
        for fig_elem in parent_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "figure")}'):
            # Skip figures that are in child sections
            if fig_elem not in child_section_figures:
                figure = self._parse_figure(fig_elem)
                if figure:
                    content['figures'].append(figure)
        
        # Extract tables (including nested ones)
        # But exclude tables that are in child sections
        child_section_tables = set()
        for child_section in child_sections:
            for table_elem in child_section.findall(f'.//{self.ns.tag(self.ns.CNXML, "table")}'):
                child_section_tables.add(table_elem)
        
        for table_elem in parent_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "table")}'):
            # Skip tables that are in child sections
            if table_elem not in child_section_tables:
                table = self._parse_table(table_elem)
                if table:
                    content['tables'].append(table)
        
        # Extract lists (including nested ones in notes, exercises, etc.)
        # But exclude lists that are in child sections
        child_section_lists = set()
        for child_section in child_sections:
            for list_elem in child_section.findall(f'.//{self.ns.tag(self.ns.CNXML, "list")}'):
                child_section_lists.add(list_elem)
        
        for list_elem in parent_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "list")}'):
            # Skip lists that are in child sections
            if list_elem not in child_section_lists:
                list_item = self._parse_list(list_elem)
                if list_item:
                    content['lists'].append(list_item)
        
        # Extract notes (including nested ones)
        # But exclude notes that are in child sections
        child_section_notes = set()
        for child_section in child_sections:
            for note_elem in child_section.findall(f'.//{self.ns.tag(self.ns.CNXML, "note")}'):
                child_section_notes.add(note_elem)
        
        for note_elem in parent_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "note")}'):
            # Skip notes that are in child sections
            if note_elem not in child_section_notes:
                note = self._parse_note(note_elem)
                if note:
                    content['notes'].append(note)
        
        # Extract exercises (including nested ones)
        # But exclude exercises that are in child sections
        child_section_exercises = set()
        for child_section in child_sections:
            for exercise_elem in child_section.findall(f'.//{self.ns.tag(self.ns.CNXML, "exercise")}'):
                child_section_exercises.add(exercise_elem)
        
        for exercise_elem in parent_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "exercise")}'):
            # Skip exercises that are in child sections
            if exercise_elem not in child_section_exercises:
                exercise = self._parse_exercise(exercise_elem)
                if exercise:
                    content['exercises'].append(exercise)
        
        return content
    
    def _parse_text_content(self, element) -> TextContent:
        """Parse text content with formatting and links"""
        text_parts = []
        emphasis_parts = []
        terms = []
        links = []
        
        def extract_text_recursive(elem):
            # Add element text
            if elem.text:
                text_parts.append(elem.text)
            
            # Process child elements
            for child in elem:
                # Handle emphasis
                if child.tag.endswith('emphasis'):
                    emphasis_text = self._extract_text_content(child)
                    text_parts.append(emphasis_text)
                    emphasis_parts.append(emphasis_text)
                
                # Handle terms
                elif child.tag.endswith('term'):
                    term_text = self._extract_text_content(child)
                    text_parts.append(term_text)
                    terms.append(term_text)
                
                # Handle links
                elif child.tag.endswith('link'):
                    link_text = self._extract_text_content(child)
                    text_parts.append(link_text)
                    links.append({
                        'text': link_text,
                        'target': child.get('target-id', ''),
                        'url': child.get('url', '')
                    })
                
                # Recurse into other elements
                else:
                    extract_text_recursive(child)
                
                # Add tail text
                if child.tail:
                    text_parts.append(child.tail)
        
        extract_text_recursive(element)
        
        return TextContent(
            text=' '.join(text_parts).strip(),
            emphasis=emphasis_parts,
            terms=terms,
            links=links
        )
    
    def _parse_figure(self, fig_elem) -> Optional[Figure]:
        """Parse a figure element"""
        fig_id = fig_elem.get('id', '')
        fig_class = fig_elem.get('class', '')
        
        # Extract caption
        caption_elem = fig_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "caption")}')
        caption = self._extract_text_content(caption_elem) if caption_elem is not None else ""
        
        # Extract media files
        media_files = []
        for media_elem in fig_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "media")}'):
            for image_elem in media_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "image")}'):
                media_files.append({
                    'type': 'image',
                    'src': image_elem.get('src', ''),
                    'mime_type': image_elem.get('mime-type', ''),
                    'width': image_elem.get('width', ''),
                    'alt': media_elem.get('alt', '')
                })
        
        if not media_files:
            return None
        
        return Figure(
            id=fig_id,
            caption=caption,
            media_files=media_files,
            class_type=fig_class
        )
    
    def _parse_table(self, table_elem) -> Optional[Table]:
        """Parse a table element"""
        table_id = table_elem.get('id', '')
        table_class = table_elem.get('class', '')
        summary = table_elem.get('summary', '')
        
        # Extract title (if present)
        title_elem = table_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "title")}')
        title = title_elem.text if title_elem is not None else ""
        
        # Extract headers and rows
        headers = []
        rows = []
        
        # Find table group
        tgroup_elem = table_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "tgroup")}')
        if tgroup_elem is not None:
            # Extract headers
            thead_elem = tgroup_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "thead")}')
            if thead_elem is not None:
                for row_elem in thead_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "row")}'):
                    header_row = []
                    for entry_elem in row_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "entry")}'):
                        header_row.append(self._extract_text_content(entry_elem))
                    if header_row:
                        headers = header_row
                        break
            
            # Extract body rows
            tbody_elem = tgroup_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "tbody")}')
            if tbody_elem is not None:
                for row_elem in tbody_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "row")}'):
                    row_data = []
                    for entry_elem in row_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "entry")}'):
                        row_data.append(self._extract_text_content(entry_elem))
                    if row_data:
                        rows.append(row_data)
        
        return Table(
            id=table_id,
            title=title,
            summary=summary,
            headers=headers,
            rows=rows,
            class_type=table_class
        )
    
    def _parse_list(self, list_elem) -> Optional[ListItem]:
        """Parse a list element"""
        list_id = list_elem.get('id', '')
        list_type = list_elem.get('list-type', 'bulleted')
        number_style = list_elem.get('number-style', 'decimal')
        
        # Extract items
        items = []
        for item_elem in list_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "item")}'):
            item_content = self._parse_text_content(item_elem)
            if item_content.text.strip():
                items.append(item_content)
        
        if not items:
            return None
        
        return ListItem(
            id=list_id,
            list_type=list_type,
            items=items,
            number_style=number_style
        )
    
    def _parse_note(self, note_elem) -> Optional[Note]:
        """Parse a note element"""
        note_id = note_elem.get('id', '')
        note_type = note_elem.get('class', 'general')
        
        # Extract content
        content = self._parse_text_content(note_elem)
        
        return Note(
            id=note_id,
            content=content,
            note_type=note_type
        )
    
    def _parse_exercise(self, exercise_elem) -> Optional[Exercise]:
        """Parse an exercise element"""
        exercise_id = exercise_elem.get('id', '')
        
        # Extract problem
        problem_elem = exercise_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "problem")}')
        if problem_elem is None:
            return None
        
        problem = self._parse_text_content(problem_elem)
        
        # Extract solution (if present)
        solution = None
        solution_elem = exercise_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "solution")}')
        if solution_elem is not None:
            solution = self._parse_text_content(solution_elem)
        
        # Extract commentary (if present)
        commentary = None
        commentary_elem = exercise_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "commentary")}')
        if commentary_elem is not None:
            commentary = self._parse_text_content(commentary_elem)
        
        return Exercise(
            id=exercise_id,
            problem=problem,
            solution=solution,
            commentary=commentary
        )
    
    def _extract_definitions(self, root) -> List[Definition]:
        """Extract all definitions from the module"""
        definitions = []
        
        for def_elem in root.findall(f'.//{self.ns.tag(self.ns.CNXML, "definition")}'):
            def_id = def_elem.get('id', '')
            
            # Extract term
            term_elem = def_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "term")}')
            term = self._extract_text_content(term_elem) if term_elem is not None else ""
            
            # Extract meaning
            meaning_elem = def_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "meaning")}')
            meaning = self._extract_text_content(meaning_elem) if meaning_elem is not None else ""
            
            if term and meaning:
                definitions.append(Definition(
                    id=def_id,
                    term=term,
                    meaning=meaning
                ))
        
        return definitions
    
    def _extract_glossary(self, root) -> List[Definition]:
        """Extract glossary terms"""
        glossary_terms = []
        
        glossary_elem = root.find(f'.//{self.ns.tag(self.ns.CNXML, "glossary")}')
        if glossary_elem is not None:
            for def_elem in glossary_elem.findall(f'.//{self.ns.tag(self.ns.CNXML, "definition")}'):
                def_id = def_elem.get('id', '')
                
                # Extract term
                term_elem = def_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "term")}')
                term = self._extract_text_content(term_elem) if term_elem is not None else ""
                
                # Extract meaning  
                meaning_elem = def_elem.find(f'.//{self.ns.tag(self.ns.CNXML, "meaning")}')
                meaning = self._extract_text_content(meaning_elem) if meaning_elem is not None else ""
                
                if term and meaning:
                    glossary_terms.append(Definition(
                        id=def_id,
                        term=term,
                        meaning=meaning,
                        context="glossary"
                    ))
        
        return glossary_terms
    
    def _extract_text_content(self, element) -> str:
        """Extract plain text content from an element"""
        if element is None:
            return ""
        
        text_parts = []
        
        # Get text from this element
        if element.text:
            text_parts.append(element.text.strip())
        
        # Recursively get text from child elements
        for child in element:
            child_text = self._extract_text_content(child)
            if child_text:
                text_parts.append(child_text)
            
            # Don't forget tail text
            if child.tail:
                text_parts.append(child.tail.strip())
        
        return ' '.join(filter(None, text_parts))
    
    def _flatten_content(self, module: Module):
        """Flatten all content for RAG processing"""
        all_text_parts = []
        
        # Add title and learning objectives
        all_text_parts.append(f"Title: {module.title}")
        if module.learning_objectives:
            all_text_parts.append("Learning Objectives:")
            for obj in module.learning_objectives:
                all_text_parts.append(f"- {obj}")
        
        # Clear the aggregate lists before flattening
        module.all_figures.clear()
        module.all_exercises.clear()
        module.all_definitions.clear()
        
        # Flatten sections
        for section in module.sections:
            self._flatten_section(section, all_text_parts, module)
        
        # Add definitions
        for definition in module.definitions + module.glossary_terms:
            all_text_parts.append(f"Definition - {definition.term}: {definition.meaning}")
            module.all_definitions.append(definition)
        
        # Set flattened content
        module.all_text = '\n\n'.join(all_text_parts)
    
    def _flatten_section(self, section: Section, text_parts: List[str], module: Module):
        """Recursively flatten a section"""
        text_parts.append(f"Section: {section.title}")
        
        # Add paragraphs
        for para in section.content:
            text_parts.append(para.text)
        
        # Add figures to module's figure list
        for figure in section.figures:
            module.all_figures.append(figure)
            text_parts.append(f"Figure {figure.id}: {figure.caption}")
        
        # Add tables
        for table in section.tables:
            text_parts.append(f"Table {table.id}: {table.title}")
            if table.summary:
                text_parts.append(f"Summary: {table.summary}")
        
        # Add lists
        for list_item in section.lists:
            text_parts.append(f"List ({list_item.list_type}):")
            for item in list_item.items:
                text_parts.append(f"- {item.text}")
        
        # Add notes
        for note in section.notes:
            text_parts.append(f"Note ({note.note_type}): {note.content.text}")
        
        # Add exercises to module's exercise list
        for exercise in section.exercises:
            module.all_exercises.append(exercise)
            text_parts.append(f"Exercise {exercise.id}: {exercise.problem.text}")
            if exercise.solution:
                text_parts.append(f"Solution: {exercise.solution.text}")
        
        # Recurse into subsections
        for subsection in section.subsections:
            self._flatten_section(subsection, text_parts, module)