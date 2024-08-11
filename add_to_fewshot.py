import pandas as pd
import json

def addToFewShot(user_input,sql_query):
    f=open("fewshot.json","r+")
    data=json.load(f)
    data["fewshots_examples"].append({"input":user_input,"query":sql_query})
    f.seek(0)
    json.dump(data,f,indent=4)
