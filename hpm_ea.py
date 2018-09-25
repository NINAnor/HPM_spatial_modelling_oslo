"""
NAME:    Computation of attributes for hedonic pricing model
         Environmental attributes

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_ea.gdb"


## input data
# sales points
v_sales_points_simple = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\input_data.gdb\sales_points_simple"

# BYM
v_bym_pm10_points = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Forurensning\BYM_luftforurensning_PM10_OB_2015.shp"
r_noise = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\NOISE\Roads.gdb\noise_day_OAF_2m_25833" 


## functions
def ExtractRasterValuesToPoints(v_points, r_values, a_name):
    v_point_values = "temp_point_values"
    
    # extract
    arcpy.gp.ExtractValuesToPoints_sa(v_points, r_values, v_point_values)

    # join values back to points
    AddFieldIfNotexists(v_points, a_name, "Double")
    join_and_copy(v_points, "JOIN_ID", v_point_values, "JOIN_ID", ["RASTERVALU"], ["{}".format(a_name)])
    arcpy.Delete_management(v_point_values)


# =========================== #
# ===== Noise pollution ===== #
# =========================== #
arcpy.AddMessage ("Computing noise...")

a_noise = "ea_noise"
a_noise1 = "ea_noise_0_60"
a_noise2 = "ea_noise_61_65"
a_noise3 = "ea_noise_66_70"
a_noise4 = "ea_noise_71_"

# extract values at sales points (lower limit of noise category)
ExtractRasterValuesToPoints(v_sales_points_simple, r_noise, a_noise)

# add fields to store binary values for categories
AddFieldIfNotexists(v_sales_points_simple, a_noise1, "Short")
AddFieldIfNotexists(v_sales_points_simple, a_noise2, "Short")
AddFieldIfNotexists(v_sales_points_simple, a_noise3, "Short")
AddFieldIfNotexists(v_sales_points_simple, a_noise4, "Short")

# compute binary values for categories
codeblock = """def classify(value, class_min, class_max):
  if(value >= class_min and value <= class_max):
    return 1
  else:
    return 0"""

arcpy.CalculateField_management(v_sales_points_simple, a_noise1, "classify(!{}!, 0, 60)".format(a_noise), "PYTHON_9.3", codeblock)
arcpy.CalculateField_management(v_sales_points_simple, a_noise2, "classify(!{}!, 61, 65)".format(a_noise), "PYTHON_9.3", codeblock)
arcpy.CalculateField_management(v_sales_points_simple, a_noise3, "classify(!{}!, 66, 70)".format(a_noise), "PYTHON_9.3", codeblock)
arcpy.CalculateField_management(v_sales_points_simple, a_noise4, "classify(!{}!, 71, 100)".format(a_noise), "PYTHON_9.3", codeblock)


# ========================== #
# ===== PM10 pollution ===== #
# ========================== #
arcpy.AddMessage ("Computing PM10...")

a_pm10 = "ea_pm10"
a_pm10_exc = "ea_pm10_exc"

# interpolate PM10 from point measurements 
r_pm10_idw = "temp_ea_pm10_idw"
arcpy.gp.Idw_sa(v_bym_pm10_points, "Value", r_pm10_idw, "2", "2", "FIXED 500", "")

# extract values at sales points
ExtractRasterValuesToPoints(v_sales_points_simple, r_pm10_idw, a_pm10)

# compute safe standards exceedings
max_pm10 = 50
AddFieldIfNotexists(v_sales_points_simple, a_pm10_exc, "Short")

codeblock = """def classify(value, class_max):
  if(value >= class_max):
    return 1
  else:
    return 0"""

arcpy.CalculateField_management(v_sales_points_simple, a_pm10_exc, "classify(!{}!, {})".format(a_pm10, max_pm10), "PYTHON_9.3", codeblock)


