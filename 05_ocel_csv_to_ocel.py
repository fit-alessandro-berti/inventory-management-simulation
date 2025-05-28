import pandas as pd
import pm4py
from datetime import datetime

first_time = datetime.fromtimestamp(10000)

ocel = pm4py.read_ocel("post_ocel_inventory_management.csv")
print(ocel)

stchange0 = ocel.relations[ocel.relations["ocel:activity"].str.startswith("ST ")][["ocel:eid", "ocel:oid"]].to_dict("records")
events0 = set(x["ocel:eid"] for x in stchange0)
stchange01 = {e: set() for e in events0}
for el in stchange0:
    stchange01[el["ocel:eid"]].add(el["ocel:oid"])

stchange = ocel.events[["ocel:eid", "ocel:activity", "ocel:timestamp", "Stock After", "Current Status"]].to_dict("records")
stchange1 = {}
for el in stchange:
    stchange1[el["ocel:eid"]] = (el["ocel:activity"], el["ocel:timestamp"], float(el["Stock After"]), el["Current Status"])

first_per_obj = ocel.relations.groupby("ocel:oid").first()["ocel:eid"].to_dict()
last_per_obj = ocel.relations.groupby("ocel:oid").last()["ocel:eid"].to_dict()
object_types = ocel.objects.groupby("ocel:oid").last()["ocel:type"].to_dict()

first_per_obj_stock = {x: stchange1[y][2] for x, y in first_per_obj.items()}
last_per_obj_stock = {x: stchange1[y][2] for x, y in last_per_obj.items()}

first_per_obj_stock_status = {x: stchange1[y][3] for x, y in first_per_obj.items()}
last_per_obj_stock_status = {x: stchange1[y][3] for x, y in last_per_obj.items()}

ocel.objects["Stock"] = ocel.objects["ocel:oid"].map(last_per_obj_stock)
ocel.objects["Status"] = ocel.objects["ocel:oid"].map(last_per_obj_stock_status)

object_changes = []

for el in first_per_obj_stock:
    object_changes.append({"ocel:oid": el, "ocel:type": object_types[el], "ocel:field": "Stock", "Stock": first_per_obj_stock[el], "ocel:timestamp": first_time})
    object_changes.append({"ocel:oid": el, "ocel:type": object_types[el], "ocel:field": "Status", "Status": first_per_obj_stock_status[el], "ocel:timestamp": first_time})

object_changes = pd.DataFrame(object_changes)
ocel.object_changes = object_changes

print(ocel.object_changes)
pm4py.write_ocel2(ocel, "post_ocel_inventory_management.xml")

ocel = pm4py.read_ocel2("post_ocel_inventory_management.xml")
print(ocel.object_changes)
