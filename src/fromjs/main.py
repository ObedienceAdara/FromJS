import os
import re
import ast
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import logging
import esprima
from esprima.nodes import Node

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JSVariable:
    name: str
    value: Any
    type: str

@dataclass
class JSFunction:
    name: str
    params: List[str]
    body: str
    is_async_func: bool = False  # Changed from is_async to is_async_func

@dataclass
class JSClass:
    name: str
    methods: List[JSFunction]
    properties: Dict[str, Any]
    constructor: Optional[JSFunction] = None

class JSImportError(Exception):
    """Custom exception for JavaScript import errors"""
    pass

class JSTypeError(Exception):
    """Custom exception for JavaScript type conversion errors"""
    pass

class JSParser:
    """Parser for JavaScript code to convert it to Python-compatible objects"""
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._cached_modules: Dict[str, Dict[str, Any]] = {}
        
    def parse_file(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """Parse a JavaScript file and return its contents as Python objects"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"JavaScript file not found: {filepath}")
            
        # Check cache first
        if str(filepath) in self._cached_modules:
            return self._cached_modules[str(filepath)]
            
        with open(filepath, 'r', encoding='utf-8') as f:
            js_code = f.read()
            
        try:
            parsed = self._parse_js_code(js_code)
            self._cached_modules[str(filepath)] = parsed
            return parsed
        except Exception as e:
            raise JSImportError(f"Failed to parse JavaScript file: {str(e)}")
    
    def _parse_js_code(self, code: str) -> Dict[str, Any]:
        """Parse JavaScript code and convert to Python objects"""
        try:
            # Parse JavaScript using esprima
            ast = esprima.parseModule(code, {'jsx': True, 'range': True, 'tokens': True})
            
            result = {
                'variables': [],
                'functions': [],
                'classes': [],
                'exports': {}  # Track exported items
            }
            
            for node in ast.body:
                if node.type == 'ExportNamedDeclaration':
                    # Handle exports
                    if node.declaration:
                        self._handle_export(node.declaration, result)
                    continue
                    
                if node.type == 'VariableDeclaration':
                    for decl in node.declarations:
                        var = self._parse_variable(decl)
                        if var:
                            result['variables'].append(var)
                            
                elif node.type == 'FunctionDeclaration':
                    func = self._parse_function(node)
                    if func:
                        result['functions'].append(func)
                        
                elif node.type == 'ClassDeclaration':
                    class_obj = self._parse_class(node)
                    if class_obj:
                        result['classes'].append(class_obj)
            
            return result
            
        except Exception as e:
            if self.strict_mode:
                raise JSImportError(f"Failed to parse JavaScript code: {str(e)}")
            logger.warning(f"Error parsing JavaScript code: {str(e)}")
            return {'variables': [], 'functions': [], 'classes': [], 'exports': {}}

    def _handle_export(self, node: Node, result: Dict[str, Any]):
        """Handle export declarations"""
        if node.type == 'VariableDeclaration':
            for decl in node.declarations:
                var = self._parse_variable(decl)
                if var:
                    result['variables'].append(var)
                    result['exports'][var.name] = var
        elif node.type == 'FunctionDeclaration':
            func = self._parse_function(node)
            if func:
                result['functions'].append(func)
                result['exports'][func.name] = func
        elif node.type == 'ClassDeclaration':
            class_obj = self._parse_class(node)
            if class_obj:
                result['classes'].append(class_obj)
                result['exports'][class_obj.name] = class_obj
    
    def _parse_variable(self, node) -> Optional[JSVariable]:
        """Parse a JavaScript variable declaration"""
        try:
            name = node.id.name if hasattr(node, 'id') else node.name
            value = self._evaluate_literal(node.init) if hasattr(node, 'init') and node.init else None
            var_type = self._determine_js_type(node.init) if hasattr(node, 'init') and node.init else 'undefined'
            return JSVariable(name=name, value=value, type=var_type)
        except Exception as e:
            if self.strict_mode:
                raise JSImportError(f"Failed to parse variable: {str(e)}")
            logger.warning(f"Error parsing variable: {str(e)}")
            return None
    
    def _parse_function(self, node) -> Optional[JSFunction]:
        """Parse a JavaScript function declaration"""
        try:
            name = node.id.name if hasattr(node, 'id') else node.name
            params = [param.name for param in node.params]
            body = self._get_node_source(node.body)
            # Changed async check to avoid keyword conflict
            is_async_func = hasattr(node, 'async') and getattr(node, 'async', False)
            return JSFunction(name=name, params=params, body=body, is_async_func=is_async_func)
        except Exception as e:
            if self.strict_mode:
                raise JSImportError(f"Failed to parse function: {str(e)}")
            logger.warning(f"Error parsing function: {str(e)}")
            return None
    
    def _parse_class(self, node) -> Optional[JSClass]:
        """Parse a JavaScript class declaration"""
        try:
            name = node.id.name if hasattr(node, 'id') else node.name
            methods = []
            properties = {}
            constructor = None
            
            for element in node.body.body:
                if element.type == 'MethodDefinition':
                    if element.kind == 'constructor':
                        constructor = self._parse_method(element)
                    else:
                        method = self._parse_method(element)
                        if method:
                            methods.append(method)
                elif element.type == 'PropertyDefinition':
                    prop_name = element.key.name
                    prop_value = self._evaluate_literal(element.value) if element.value else None
                    properties[prop_name] = prop_value
            
            return JSClass(name=name, methods=methods, properties=properties, constructor=constructor)
        except Exception as e:
            if self.strict_mode:
                raise JSImportError(f"Failed to parse class: {str(e)}")
            logger.warning(f"Error parsing class: {str(e)}")
            return None
    
    def _parse_method(self, node) -> Optional[JSFunction]:
        """Parse a class method definition"""
        try:
            name = node.key.name
            params = [param.name for param in node.value.params]
            body = self._get_node_source(node.value.body)
            # Changed async check to avoid keyword conflict
            is_async_func = hasattr(node.value, 'async') and getattr(node.value, 'async', False)
            return JSFunction(name=name, params=params, body=body, is_async_func=is_async_func)
        except Exception as e:
            if self.strict_mode:
                raise JSImportError(f"Failed to parse method: {str(e)}")
            logger.warning(f"Error parsing method: {str(e)}")
            return None
    
    def _evaluate_literal(self, node) -> Any:
        """Evaluate a JavaScript literal value"""
        if not node:
            return None
            
        if node.type == 'Literal':
            return node.value
        elif node.type == 'ObjectExpression':
            obj = {}
            for prop in node.properties:
                key = prop.key.name if prop.key.type == 'Identifier' else prop.key.value
                value = self._evaluate_literal(prop.value)
                obj[key] = value
            return obj
        elif node.type == 'ArrayExpression':
            return [self._evaluate_literal(element) for element in node.elements if element is not None]
        elif node.type == 'Identifier':
            return node.name  # Return identifier name as is
        elif node.type == 'TemplateLiteral':
            # Basic template literal support
            return ''.join(self._evaluate_literal(elem) for elem in node.quasis)
        return None
    
    def _determine_js_type(self, node) -> str:
        """Determine the JavaScript type of a node"""
        if not node:
            return 'undefined'
            
        if node.type == 'Literal':
            return type(node.value).__name__
        elif node.type == 'ObjectExpression':
            return 'object'
        elif node.type == 'ArrayExpression':
            return 'array'
        elif node.type == 'FunctionExpression':
            return 'function'
        elif node.type == 'ArrowFunctionExpression':
            return 'function'
        elif node.type == 'Identifier':
            return 'identifier'
        elif node.type == 'TemplateLiteral':
            return 'string'
        return 'unknown'
    
    def _get_node_source(self, node) -> str:
        """Get the source code of a node"""
        try:
            if hasattr(node, 'source'):
                return node.source()
            elif isinstance(node, dict) and 'type' in node:
                return json.dumps(node)
            return str(node)
        except Exception:
            return str(node)

class JSModule:
    """Wrapper class for imported JavaScript modules"""
    
    def __init__(self, parsed_content: Dict[str, Any]):
        self._content = parsed_content
        self._setup_attributes()
    
    def _setup_attributes(self):
        """Set up Python attributes from parsed JavaScript content"""
        # Set up variables
        for var in self._content.get('variables', []):
            setattr(self, var.name, var.value)
        
        # Set up functions
        for func in self._content.get('functions', []):
            setattr(self, func.name, self._create_function_wrapper(func))
        
        # Set up classes
        for cls in self._content.get('classes', []):
            setattr(self, cls.name, self._create_class_wrapper(cls))
            
        # Set up exports
        for name, item in self._content.get('exports', {}).items():
            if not hasattr(self, name):
                if isinstance(item, JSFunction):
                    setattr(self, name, self._create_function_wrapper(item))
                elif isinstance(item, JSClass):
                    setattr(self, name, self._create_class_wrapper(item))
                elif isinstance(item, JSVariable):
                    setattr(self, name, item.value)
    
    def _create_function_wrapper(self, func: JSFunction):
        """Create a Python wrapper for a JavaScript function"""
        def wrapper(*args, **kwargs):
            # TODO: Implement actual JavaScript execution
            # For now, just log the call and return None
            params = ', '.join([str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()])
            logger.info(f"Called JavaScript function {func.name}({params})")
            return None
        
        wrapper.__name__ = func.name
        wrapper.__doc__ = f"JavaScript function {func.name}({', '.join(func.params)})"
        return wrapper
    
    def _create_class_wrapper(self, cls: JSClass):
        """Create a Python wrapper for a JavaScript class"""
        class_dict = {
            '__doc__': f"JavaScript class {cls.name}",
            '__init__': self._create_constructor_wrapper(cls.constructor) if cls.constructor else lambda self: None,
        }
        
        # Add methods
        for method in cls.methods:
            class_dict[method.name] = self._create_method_wrapper(method)
        
        # Add properties
        for prop_name, prop_value in cls.properties.items():
            class_dict[prop_name] = prop_value
        
        return type(cls.name, (object,), class_dict)
    
    def _create_constructor_wrapper(self, constructor: Optional[JSFunction]):
        """Create a Python wrapper for a JavaScript class constructor"""
        def wrapper(self, *args, **kwargs):
            # TODO: Implement actual JavaScript constructor execution
            params = ', '.join([str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()])
            logger.info(f"Called JavaScript constructor with params ({params})")
            
            # Store constructor arguments as instance attributes
            for param, arg in zip(constructor.params, args):
                setattr(self, param, arg)
            for key, value in kwargs.items():
                setattr(self, key, value)
                
        return wrapper
    
    def _create_method_wrapper(self, method: JSFunction):
        """Create a Python wrapper for a JavaScript class method"""
        def wrapper(self, *args, **kwargs):
            # TODO: Implement actual JavaScript method execution
            params = ', '.join([str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()])
            logger.info(f"Called JavaScript method {method.name}({params})")
            return None
        
        wrapper.__name__ = method.name
        wrapper.__doc__ = f"JavaScript method {method.name}({', '.join(method.params)})"
        return wrapper

def import_js(filepath: Union[str, Path], strict_mode: bool = True) -> JSModule:
    """
    Import a JavaScript file and return it as a Python module.
    """
    parser = JSParser(strict_mode=strict_mode)
    parsed_content = parser.parse_file(filepath)
    return JSModule(parsed_content) 