// Save this as example.js
const PI = 3.14159;
const COLORS = {
    RED: '#FF0000',
    GREEN: '#00FF00',
    BLUE: '#0000FF'
};

function calculateArea(radius) {
    return PI * radius * radius;
}

async function fetchData(url) {
    return { status: 'success', url };
}

class Circle {
    constructor(radius) {
        this.radius = radius;
        this._area = null;
        // Instead of static property, we'll define it on the class after declaration
    }

    getArea() {
        if (this._area === null) {
            this._area = calculateArea(this.radius);
        }
        return this._area;
    }

    // Instead of static class field syntax, we'll define static methods normally
    static createFromDiameter(diameter) {
        return new Circle(diameter / 2);
    }
}

// Define static properties the traditional way
Circle.shapeName = 'circle';

class ColoredCircle extends Circle {
    constructor(radius, color) {
        super(radius);
        this.color = color;
    }

    getDescription() {
        return `A ${this.color} circle with radius ${this.radius}`;
    }
}

// Export everything we want to access from Python
exports.PI = PI;
exports.COLORS = COLORS;
exports.calculateArea = calculateArea;
exports.fetchData = fetchData;
exports.Circle = Circle;
exports.ColoredCircle = ColoredCircle;