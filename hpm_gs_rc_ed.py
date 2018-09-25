"""
NAME:    Computation of attributes for hedonic pricing model
         Green structure - recreation areas - euclidean distances

AUTHOR(S): Zofie Cimburova < zofie.cimburova AT nina.no>
"""

"""
To Dos:
"""

import arcpy
import math  
from arcpy import env
from arcpy.sa import *
from helpful_functions import *
  
## environment settings
env.overwriteOutput = True
env.outputCoordinateSystem = arcpy.SpatialReference("ETRS 1989 UTM Zone 33N")
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\NIBIO\fkb_ar5_OK_2m.tif"
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_rc.gdb"


## input data
# sales points
v_sales_points_simple = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\input_data.gdb\sales_points_simple"

# FKB
v_fkb_water = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\FKB\Basisdata_0301_Oslo_5972_FKB-Vann_FGDB.gdb\fkb_vann_omrade"
l_fkb_water = arcpy.MakeFeatureLayer_management (v_fkb_water, "l_fkb_water")

# Periurban forest by Megan
v_forest = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\Hedonics\Xianwen_Chen\Inputs\AR5_periUrbanForest_25833.shp"
l_forest = arcpy.MakeFeatureLayer_management (v_forest, "l_forest")

# Green spaces within built area
v_green_fkb = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_rc.gdb\fkb_arealbruk_selected_OB"
v_green_ar5 = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_rc.gdb\fkb_ar5_selected_OB"

v_fkb_green = "fkb_green_OB"
#arcpy.Merge_management([v_green_fkb, v_green_ar5], v_fkb_green)

v_fkb_green_dissolve = "fkb_green_dissolve_OB"
#arcpy.Dissolve_management(v_fkb_green, v_fkb_green_dissolve, dissolve_field="", statistics_fields="", multi_part="SINGLE_PART", unsplit_lines="DISSOLVE_LINES")
l_fkb_green_dissolve = arcpy.MakeFeatureLayer_management(v_fkb_green_dissolve, "l_fkb_green_dissolve")


## functions
def EuclideanDistanceToFeature(v_feature, v_points, feature_type_name):
    r_distance = "temp_{}_distance_raster".format(feature_type_name)
    a_distance = "gs_rc_ed_{}".format(feature_type_name)
    
    # compute distance raster 
    arcpy.AddMessage("  Computing distance raster...")
    arcpy.gp.EucDistance_sa(v_feature, r_distance, "", "2", "")
    
    # extract values at sales points
    arcpy.AddMessage("  Extracting values at points...")
    ExtractRasterValuesToPoints(v_points, r_distance, a_distance)

def ExtractRasterValuesToPoints(v_points, r_values, a_name):
    v_point_values = "temp_point_values"
    
    # extract
    arcpy.gp.ExtractValuesToPoints_sa(v_points, r_values, v_point_values)

    # join values back to points
    AddFieldIfNotexists(v_points, a_name, "Double")
    join_and_copy(v_points, "JOIN_ID", v_point_values, "JOIN_ID", ["RASTERVALU"], ["{}".format(a_name)])
    arcpy.Delete_management(v_point_values)


# ======================================= #
# ===== Rivers, lakes, sea distance ===== #
# ======================================= #
for water_element in ["lake", "river", "sea"]:
    arcpy.AddMessage ("Computing {}...".format(water_element))
    
    # extract features from FKB
    if water_element == "lake":
        arcpy.SelectLayerByAttribute_management (l_fkb_water, "NEW_SELECTION", "objtype = 'Innsjo' AND Shape_Area > 10000")
    elif water_element == "river":
        arcpy.SelectLayerByAttribute_management (l_fkb_water, "NEW_SELECTION", "objtype = 'ElvBekk'")
    else:
        arcpy.SelectLayerByAttribute_management (l_fkb_water, "NEW_SELECTION", "objtype = 'Havflate'")
    
    EuclideanDistanceToFeature(l_fkb_water, v_sales_points_simple, water_element)

 

    
# ============================ #
# ===== Periurban forest ===== #
# ============================ #    
arcpy.AddMessage ("Computing periurban forest...")

# extract periurban forest
arcpy.SelectLayerByAttribute_management (l_forest, "NEW_SELECTION", "PeriUrban = 'Yes'")
EuclideanDistanceToFeature(l_forest, v_sales_points_simple, "forest")


# ========================= #
# ===== City greenery ===== #
# ========================= #    
arcpy.AddMessage ("Computing city greenery...")

# extract greenery larger than 5000 m2
arcpy.SelectLayerByAttribute_management (l_fkb_green_dissolve, "NEW_SELECTION", "Shape_Area > 5000")
EuclideanDistanceToFeature(l_fkb_green_dissolve, v_sales_points_simple, "park")

