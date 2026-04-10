import os
import sys
import json
import math
import random


import datetime  # unused



def compute(a,b):
    x= a+b
    y =a*b
    return x,y


def long_line():
    return "this is a very very very very very very very very very very very long line that black should wrap nicely"


def save_result(path,data):
    folder=os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    with open(path,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2)


def main():

    numbers=[random.randint(0,10) for _ in range(20)]

    s=0
    for n in numbers:
        if n%2==0:
            s += n
        else:
            s += n*2

    a,b = compute(3,5)
    result = {"sum": s, "a": a, "b": b, "sqrt": math.sqrt(16)}
    save_result("tmp_simple_demo.json", result)

    print(long_line())
    print("done", result)


if __name__ == "__main__":
    main()
