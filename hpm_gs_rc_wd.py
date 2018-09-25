"""
NAME:    Computation of attributes for hedonic pricing model
         Green structure - recreation areas - walking distances

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
  
## workspace settings
env.overwriteOutput = True
env.outputCoordinateSystem = arcpy.SpatialReference("ETRS 1989 UTM Zone 33N")
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OK_oslo_kommune.shp"
env.cellSize = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\SENTINEL\s2_lc_OAF_08_2017_10m_25833.tif"
env.snapRaster = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\SENTINEL\s2_lc_OAF_08_2017_10m_25833.tif"
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_rc.gdb"
   
## input data
# sales points
v_sales_points_simple = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\input_data.gdb\sales_points_simple"

AddFieldIfNotexists(v_sales_points_simple, "gs_rc_wd_garden", "Double")
AddFieldIfNotexists(v_sales_points_simple, "gs_rc_wd_cemet", "Double")
AddFieldIfNotexists(v_sales_points_simple, "gs_rc_wd_friom", "Double")

# localities
v_kolonihage = "kolonihage_OK_polygon"

v_fkb_arealbruk = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\FKB\Basisdata_0301_Oslo_5972_FKB-Arealbruk_FGDB.gdb\fkb_arealbruk_omrade"

v_gravplass = "FKB_gravplass_OK_polygon"
arcpy.FeatureClassToFeatureClass_conversion(v_fkb_arealbruk, r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_rc.gdb", v_gravplass, "objtype = 'Gravplass'")

v_friomrade = r"friomrade_OK_polygon"

# ============================================================ #
# ===== prepare datasets for computing walking distances ===== #
# ============================================================ #

## Prepare facilities
prepare_data = 0
if prepare_data == 1:
    arcpy.AddMessage("Preparing facilities...")

    # add field to store number of points
    AddFieldIfNotexists(v_kolonihage, "random_pt_cnt", "Short")
    AddFieldIfNotexists(v_gravplass, "random_pt_cnt", "Short")
    AddFieldIfNotexists(v_friomrade, "random_pt_cnt", "Short")
    
    arcpy.CalculateField_management(v_kolonihage, "random_pt_cnt", "math.ceil(!Shape_Area!/400)", "PYTHON_9.3")
    arcpy.CalculateField_management(v_gravplass, "random_pt_cnt", "math.ceil(!Shape_Area!/400)", "PYTHON_9.3")
    arcpy.CalculateField_management(v_friomrade, "random_pt_cnt", "math.ceil(!Shape_Area!/400)", "PYTHON_9.3")

    # randomly assign points
    v_kolonihage_points_temp = "temp_kolonihage_pt"
    v_gravplass_points_temp = "temp_gravplass_pt"
    v_friomrade_points_temp = "temp_friomrade_pt"

    arcpy.CreateRandomPoints_management("C:/Users/zofie.cimburova/OneDrive - NINA/URBAN_EEA/HPM VARIABLES/DATA/data_gs_rc.gdb", v_kolonihage_points_temp, v_kolonihage, "", "random_pt_cnt", minimum_allowed_distance="10 Meters")
    arcpy.CreateRandomPoints_management("C:/Users/zofie.cimburova/OneDrive - NINA/URBAN_EEA/HPM VARIABLES/DATA/data_gs_rc.gdb", v_gravplass_points_temp, v_gravplass, "", "random_pt_cnt", minimum_allowed_distance="10 Meters")
    arcpy.CreateRandomPoints_management("C:/Users/zofie.cimburova/OneDrive - NINA/URBAN_EEA/HPM VARIABLES/DATA/data_gs_rc.gdb", v_friomrade_points_temp, v_friomrade, "", "random_pt_cnt", minimum_allowed_distance="10 Meters")
    
    # assign ID of facility
    v_kolonihage_points = "kolonihage_OK_point"
    v_gravplass_points = "gravplass_OK_point"
    v_friomrade_points = "friomrade_OK_point"
    
    arcpy.Intersect_analysis([v_kolonihage_points_temp, v_kolonihage], v_kolonihage_points, join_attributes="ONLY_FID")
    arcpy.Intersect_analysis([v_gravplass_points_temp, v_gravplass], v_gravplass_points, join_attributes="ONLY_FID")
    arcpy.Intersect_analysis([v_friomrade_points_temp, v_friomrade], v_friomrade_points, join_attributes="ONLY_FID")
    
    arcpy.Delete_management(v_kolonihage_points_temp)
    arcpy.Delete_management(v_gravplass_points_temp)
    arcpy.Delete_management(v_friomrade_points_temp)


# 1. segment map of Oslo must be in feature dataset within geodatabase
# 2. new network dataset - no turns
#                        - no elevation
# 3. new closest facility layer - facilities = v_kolonihage_points, name = FID_kolonihage_OK_polygon, Use Geometry
#                               - incidents = v_sales_points_simple, name = JOIN_ID, Use Geometry
# 4. Solve
# 5. Export Routes as feature class - wd_kolonihage

join_data = 1
if join_data == 1:
    arcpy.AddMessage("Joining distance to simple sales points...")
    
    v_kolonihage_routes = "wd_kolonihage"
    v_gravplass_routes = "wd_gravplass"
    v_friomrade_routes = "wd_friomrade"

    AddFieldIfNotexists(v_kolonihage_routes, "simple_sales_pt_ID", "Long")
    AddFieldIfNotexists(v_gravplass_routes, "simple_sales_pt_ID", "Long")
    AddFieldIfNotexists(v_friomrade_routes, "simple_sales_pt_ID", "Long")
   
    arcpy.CalculateField_management(v_kolonihage_routes, "simple_sales_pt_ID", "int(!Name!.split(\" - \")[0])", "PYTHON_9.3")
    arcpy.CalculateField_management(v_gravplass_routes, "simple_sales_pt_ID", "int(!Name!.split(\" - \")[0])", "PYTHON_9.3")
    arcpy.CalculateField_management(v_friomrade_routes, "simple_sales_pt_ID", "int(!Name!.split(\" - \")[0])", "PYTHON_9.3")

    join_and_copy(v_sales_points_simple, "JOIN_ID", v_kolonihage_routes, "simple_sales_pt_ID", ["Total_Length"], ["gs_rc_wd_garden"])
    join_and_copy(v_sales_points_simple, "JOIN_ID", v_gravplass_routes, "simple_sales_pt_ID", ["Total_Length"], ["gs_rc_wd_cemet"])
    join_and_copy(v_sales_points_simple, "JOIN_ID", v_friomrade_routes, "simple_sales_pt_ID", ["Total_Length"], ["gs_rc_wd_friom"])

   
