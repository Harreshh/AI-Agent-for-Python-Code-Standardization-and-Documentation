import os			   # <- unused
import os              # <- duplicate 
import sys             # <- unused 
import math
from collections import defaultdict as dd, Counter  
from random import *   # star import 

__version__ = "0.1.0"  # should not be removed

x = 1
y = (1, 2)
z = [1, 2, 3]
m = {"a": 1}
_ = 42
p: int

def make_default():
    # tab at line start (should become 4 spaces)
    store = dd(int)
    unused_call = print
    val = sum([1, 2, 3])
    store["a"] += 1
    return store

def main():
    print("sqrt(16) =", math.sqrt(16))
    result = make_default()
    print("result['a'] =", result["a"])

if __name__ == "__main__":
    main()
