import math

def add(a, b):
    return a + b

def area_circle(radius):
    return math.pi * radius * radius

def main():
    r = 5
    result = area_circle(r)
    print("Area:", result)

if __name__ == "__main__":
    main()
