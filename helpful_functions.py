"""
NAME:    Useful functions

AUTHOR(S): Zofie Cimburova < zofie.cimburova AT nina.no>
"""

"""
To Dos:
"""

import arcpy
import math  
import itertools  
import datetime  
 
# =========================== #
# Check if field exists
# =========================== #
def FieldExist(featureclass, fieldname):
    fieldList = arcpy.ListFields(featureclass, fieldname)
    fieldCount = len(fieldList)
 
    if (fieldCount == 1):
        return True
    else:
        return False
 
         
# =========================== #
# Add field if not already exists
# =========================== #
def AddFieldIfNotexists(featureclass, fieldname, type):
    if (not FieldExist(featureclass, fieldname)):
        arcpy.AddField_management(featureclass, fieldname, type)
          
          
# =========================== #
# Join table 2 to table 1 and copy source field from table 2 to destination field of table 1
# =========================== #
def join_and_copy(table1, join_field1, table2, join_field2, source_fields, dest_fields):
     
    name1 = arcpy.Describe(table1).name
    name2 = arcpy.Describe(table2).name
     
    # 1. create layer from table1
    layer1 = "table1_lyr"
    arcpy.MakeFeatureLayer_management(table1, layer1)
     
    # 2. create Join
    arcpy.AddJoin_management(layer1, join_field1, table2, join_field2)
            
    i = 0
    for source_field in source_fields:
        #arcpy.AddMessage("Copying values from " + name2 +  "." + source_fields[i] + " to " + name1 + "." + dest_fields[i])
        arcpy.CalculateField_management(layer1, name1 + "." + dest_fields[i], "[" + name2 + "." + source_fields[i] + "]")
        i = i+1
        