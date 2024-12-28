# FromJS

A Python library for parsing and executing JavaScript code within Python applications.

## Installation

```bash
pip install FromJS
```

## Usage

```python
from FromJS import import_js

# Import a JavaScript file
js_module = import_js('path/to/your/javascript/file.js')

# Use the imported JavaScript functionality
result = js_module.some_function()
```

## Features

- Parse JavaScript files and convert to Python objects
- Support for JavaScript variables, functions, and classes
- Handle ES6+ syntax including async/await
- Export management

## License

This project is licensed under the MIT License - see the LICENSE file for details.