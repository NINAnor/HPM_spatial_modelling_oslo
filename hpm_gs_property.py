"""
NAME:    Computation of attributes for hedonic pricing model
         Green structure - property

AUTHOR(S): Zofie Cimburova < zofie.cimburova AT nina.no>
"""

"""
To Dos:
"""

import arcpy
import time
import math  

from arcpy import env
from arcpy.sa import *
from helpful_functions import *
  

# workspace settings
env.overwriteOutput = True
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_property.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("ETRS 1989 UTM Zone 33N")
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OK_oslo_kommune.shp"

## input data
# sales points
v_sales_points = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\input_data.gdb\sales_points_simple" 

AddFieldIfNotexists(v_sales_points, "gs_prop_tree", "Double")
AddFieldIfNotexists(v_sales_points, "gs_prop_grass", "Double")
AddFieldIfNotexists(v_sales_points, "gs_prop_water", "Short")

# S2 landcover
inp_landcover = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\SENTINEL\sentinel.gdb\s2_lc_OAF_08_2015_10m_vector"

# FKB
v_fkb_water = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\FKB\Basisdata_0301_Oslo_5972_FKB-Vann_FGDB.gdb\fkb_vann_omrade"
l_fkb_water = arcpy.MakeFeatureLayer_management (v_fkb_water, "l_fkb_water")

# parcels
v_properties = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\CADASTRE\cadastre.gdb\eiendom_OK" 

# select only parcels which intersect sales points
l_parcels = arcpy.MakeFeatureLayer_management (v_properties, "l_parcels")
arcpy.SelectLayerByLocation_management (l_parcels, "INTERSECT", v_sales_points, "", "NEW_SELECTION")

v_properties_selected = "temp_gs_parcels_select"
arcpy.FeatureClassToFeatureClass_conversion(l_parcels, r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_property.gdb", v_properties_selected)
AddFieldIfNotexists(v_properties_selected, "JOIN_ID", "Long")
arcpy.CalculateField_management(v_properties_selected, "JOIN_ID", "[OBJECTID]")


# =========================================== #
# ===== Sentinel-2 tree and grass cover ===== #
# =========================================== #

for s2_class in ["GRASS","FOREST"]:
    arcpy.AddMessage("Computing {}".format(s2_class))

    # 1. SELECT LANDCOVER CLASS
    if s2_class == "GRASS":
        selection_formula = "gridcode = 2"
    elif s2_class == "FOREST":
        selection_formula = "gridcode = 4"
    
    inp_lc_layer = arcpy.MakeFeatureLayer_management (inp_landcover, "temp_layer")
    arcpy.SelectLayerByAttribute_management (inp_lc_layer, "NEW_SELECTION", selection_formula)
    arcpy.AddMessage("  Features from land cover class selected.")

    # 2. INTERSECT LANDCOVER AND PARCELS
    v_intersect = "intersect_{}".format(s2_class)
    arcpy.Intersect_analysis([inp_lc_layer, v_properties_selected],v_intersect,"","","")
    arcpy.AddMessage("  Intersection done.")

    # 3. SUMMARIZE AREA OF LANDCOVER PER AREA
    t_summary = "summary_{}".format(s2_class)
    field_fid = "FID_{}".format(v_properties_selected)
    arcpy.Statistics_analysis(v_intersect, t_summary, [["Shape_Area", "SUM"]], field_fid)
    
    arcpy.Delete_management(v_intersect)
    arcpy.AddMessage("  Summary table created.")

    # 4. ADD FIELD to store area
    # 5. ADD FIELD to store percentage
    field_area = "AREA_{}".format(s2_class)
    field_perc = "PERC_{}".format(s2_class)
    
    AddFieldIfNotexists(v_properties_selected, field_area, "Double")
    AddFieldIfNotexists(v_properties_selected, field_perc, "Double")
    arcpy.AddMessage("  Fields added.")

    # 6. JOIN area, summarize ON OBJECTID = FID_area
    cnt = int(arcpy.GetCount_management(t_summary)[0])
    if cnt > 0:  
        join_and_copy(v_properties_selected, "JOIN_ID", t_summary, field_fid, ["Sum_Shape_Area"], [field_area])
    
    arcpy.Delete_management(t_summary)
    arcpy.AddMessage("  Field area copied.")

    # 7. CALCULATE FIELD AREA
    expression = "replaceNull(!{}!,!Shape_Area!)".format(field_area)
    codeblock = """def replaceNull(Green_Area, Shape_Area):
        if Green_Area == None:
            return '0'
        elif Green_Area > Shape_Area:
            return Shape_Area
        else:
            return Green_Area"""  

    arcpy.CalculateField_management(v_properties_selected, field_area, expression, "PYTHON_9.3", codeblock)
    arcpy.AddMessage("  Field area computed.")

    # 8. CALCULATE FIELD PERCENTAGE
    arcpy.CalculateField_management(v_properties_selected, field_perc, '!{}!/!Shape_Area!'.format(field_area), "PYTHON_9.3")
    arcpy.AddMessage("  Field percentage computed.")

arcpy.AddMessage("Fields percentage and area computed.")

# 9. JOIN TO SALES POINTS
v_join = "temp_gs_parcels_join"
arcpy.SpatialJoin_analysis(v_sales_points, v_properties_selected, v_join, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT")   

# RATHER DO THIS MANUALLY
join_and_copy(v_sales_points, "JOIN_ID", v_join, "JOIN_ID", ["PERC_GRASS", "PERC_FOREST"], ["gs_prop_grass", "gs_prop_tree"])

# 10. DELETE
arcpy.Delete_management(v_properties_selected)
arcpy.Delete_management(v_join)


# ============================ #
# ===== FKB water bodies ===== #
# ============================ #

# 1. Create 10m buffer of selected properties
v_prop_buff = "temp_prop_buff"
arcpy.Buffer_analysis(v_properties_selected, v_prop_buff, "10 meters")

# 2. Add field to store water edge 0/1
AddFieldIfNotexists(v_prop_buff, "gs_prop_water", "Short")
arcpy.CalculateField_management(v_prop_buff, "gs_prop_water", "0")

# 3. Select waterbodies
arcpy.SelectLayerByAttribute_management (l_fkb_water, "NEW_SELECTION", "objtype IN ('Innsjo', 'ElvBekk', 'Havflate')")

# 4. Select buffered properties intersecting with selected water bodies and assign attribute 1
l_prop_buff = arcpy.MakeFeatureLayer_management (v_prop_buff, "l_prop_buff")
arcpy.SelectLayerByLocation_management(l_prop_buff, "INTERSECT", l_fkb_water, "", "NEW_SELECTION")
arcpy.CalculateField_management(l_prop_buff, "gs_prop_water", "1")

# 5. JOIN TO SALES POINTS
v_join = "temp_gs_parcels_join"
arcpy.SpatialJoin_analysis(v_sales_points, v_prop_buff, v_join, "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT")   
join_and_copy(v_sales_points, "JOIN_ID", v_join, "JOIN_ID", ["gs_prop_water_1"], ["gs_prop_water"])

# 10. DELETE
arcpy.Delete_management(v_prop_buff)
arcpy.Delete_management(v_join)



