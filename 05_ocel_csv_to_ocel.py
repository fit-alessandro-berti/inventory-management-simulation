import pm4py

ocel = pm4py.read_ocel("post_ocel_inventory_management.csv")
print(ocel)
pm4py.write_ocel2(ocel, "post_ocel_inventory_management.xml")
