import pandas as pd
import pm4py
from datetime import datetime

first_time = datetime.fromtimestamp(0)

ocel = pm4py.read_ocel("post_ocel_inventory_management.csv")
print(ocel)
print(ocel.events.columns)

stchange0 = ocel.relations[ocel.relations["ocel:activity"].str.startswith("ST ")][["ocel:eid", "ocel:oid"]].to_dict("records")
events0 = set(x["ocel:eid"] for x in stchange0)
stchange01 = {e: set() for e in events0}
for el in stchange0:
    stchange01[el["ocel:eid"]].add(el["ocel:oid"])

stchange = ocel.events[["ocel:eid", "ocel:activity", "ocel:timestamp", "Stock After", "Current Status", "Safety Stock (SS)", "OS"]].to_dict("records")
stchange1 = {}
for el in stchange:
    stchange1[el["ocel:eid"]] = (el["ocel:activity"], el["ocel:timestamp"], float(el["Stock After"]), el["Current Status"], el["Safety Stock (SS)"], el["OS"])

first_per_obj = ocel.relations.groupby("ocel:oid").first()["ocel:eid"].to_dict()
last_per_obj = ocel.relations.groupby("ocel:oid").last()["ocel:eid"].to_dict()
object_types = ocel.objects.groupby("ocel:oid").last()["ocel:type"].to_dict()

first_per_obj_stock = {x: stchange1[y][2] for x, y in first_per_obj.items()}
first_per_obj_stock_status = {x: stchange1[y][3] for x, y in first_per_obj.items()}
first_per_obj_ss = {x: stchange1[y][4] for x, y in first_per_obj.items()}
first_per_obj_os = {x: stchange1[y][5] for x, y in first_per_obj.items()}

ocel.objects["Stock"] = ocel.objects["ocel:oid"].map(first_per_obj_stock)
ocel.objects["Status"] = ocel.objects["ocel:oid"].map(first_per_obj_stock_status)
ocel.objects["SS"] = ocel.objects["ocel:oid"].map(first_per_obj_ss)
ocel.objects["OS"] = ocel.objects["ocel:oid"].map(first_per_obj_os)

object_changes = []

#for el in first_per_obj_stock:
#object_changes.append({"ocel:oid": el, "ocel:type": object_types[el], "ocel:field": "Stock", "Stock": first_per_obj_stock[el], "ocel:timestamp": first_time})
#object_changes.append({"ocel:oid": el, "ocel:type": object_types[el], "ocel:field": "Status", "Status": first_per_obj_stock_status[el], "ocel:timestamp": first_time})

for x, y in stchange01.items():
    status = stchange1[x][3]
    stock = stchange1[x][2]
    timestamp = stchange1[x][1]

    if timestamp > first_time:
        for obj in y:
            if first_per_obj[obj] != last_per_obj[obj]:
                object_changes.append({"ocel:oid": obj, "ocel:type": object_types[obj], "ocel:field": "Stock", "Stock": stock, "ocel:timestamp": timestamp})
                object_changes.append({"ocel:oid": obj, "ocel:type": object_types[obj], "ocel:field": "Status", "Status": status, "ocel:timestamp": timestamp})

object_changes = pd.DataFrame(object_changes)
object_changes.sort_values(["ocel:oid", "ocel:timestamp"], inplace=True)
ocel.object_changes = object_changes

print(ocel.object_changes)
pm4py.write_ocel2(ocel, "post_ocel_inventory_management.xml")

ocel = pm4py.read_ocel2("post_ocel_inventory_management.xml")
print(ocel.object_changes)

print(ocel.objects)
print(ocel.objects.columns)
