import pm4py

ocel = pm4py.read_ocel("ocel_inventory_management.csv")
print(ocel)
pm4py.write_ocel2(ocel, "ocel_inventory_management.xml")
