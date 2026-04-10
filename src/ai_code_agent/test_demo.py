import os, json
import math
import random
import numpy as np
import pandas as pd
import requests


def compute(a,b):
 x=a+b
 y= a*b
 return x,y


def long_line( ):
 return "this is a very very very very very very very very very very very long line that should wrap nicely"


def stats_with_numpy(numbers ):
    arr=np.array(numbers)
    return {"mean":float(np.mean(arr)),"std":float(np.std(arr)),"max":int(np.max(arr))}


def create_dataframe(numbers):
 df = pd.DataFrame({"values":numbers})
 df["squared"]=df["values"]**2
 return df


def fetch_data( ):
    try:
        r = requests.get("https://api.github.com")
        return {"status_code":r.status_code}
    except:
     return {"status_code":"error"}


def save_result(path,data):
 folder=os.path.dirname(path)
 if folder and not os.path.exists(folder):
        os.makedirs(folder)

 with open(path,"w",encoding="utf-8") as f:
  json.dump(data,f,indent=2)


def main( ):

 numbers=[random.randint(0,10) for _ in range(20)]

 s=0
 for n in numbers:
  if n%2==0:
   s+=n
  else:
    s+=n*2

 a,b=compute(3,5)

 stats=stats_with_numpy(numbers)
 df=create_dataframe(numbers)
 api=fetch_data()

 result={"sum":s,"a":a,"b":b,"sqrt":math.sqrt(16),"stats":stats,"api":api}

 save_result("tmp_simple_demo.json",result)

 print(long_line())
 print(df.head())
 print("done",result)


if _name=="main_":
 main()