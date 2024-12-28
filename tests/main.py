import logging
from pathlib import Path
from poly import import_js

# Configure logging to see the function calls
logging.basicConfig(level=logging.INFO)

def main():
    try:
        # Make sure to use the correct path to your example.js file
        script_dir = Path(__file__).parent
        js_file = script_dir / "example.js"
        js_module = import_js(js_file)

        # Test the imported module
        print(f"PI = {js_module.PI}")
        print(f"COLORS = {js_module.COLORS}")

        # Test function
        area = js_module.calculateArea(5)
        print(f"Area of circle with radius 5 = {area}")

        # Test class
        circle = js_module.Circle(3)
        circle_area = circle.getArea()
        print(f"Circle area = {circle_area}")
        print(f"Circle radius = {circle.radius}")

        # Test Async function
        data = js_module.fetchData('https://google.com')


    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()