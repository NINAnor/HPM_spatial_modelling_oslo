"""
NAME:    Computation of attributes for hedonic pricing model
         Location attributes

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_la.gdb"
env.outputCoordinateSystem = arcpy.SpatialReference("ETRS 1989 UTM Zone 33N")
env.overwriteOutput = True
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\NIBIO\fkb_ar5_OK_2m.tif"


## input data
# sales points
v_sales_points_simple = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\input_data.gdb\sales_points_simple"

# FKB buildings
v_fkb_buildings = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\FKB\Basisdata_0301_Oslo_5972_FKB-Bygning_FGDB.gdb\fkb_bygning_omrade"
l_fkb_buildings = arcpy.MakeFeatureLayer_management (v_fkb_buildings, "temp_layer1")       

# OSM points of interest
v_osm_poi_point = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\OSM\NORWAY_2017_11_08_GEOFABRIK\osm_pois_free_1.shp"
l_osm_poi_point = arcpy.MakeFeatureLayer_management (v_osm_poi_point, "temp_layer2")   

v_osm_poi_area = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\OSM\NORWAY_2017_11_08_GEOFABRIK\osm_pois_a_free_1.shp"
l_osm_poi_area = arcpy.MakeFeatureLayer_management (v_osm_poi_area, "temp_layer3")

# OSM transport   
v_osm_transport = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\OSM\NORWAY_2017_11_08_GEOFABRIK\osm_transport_free_1.shp"
l_osm_transport = arcpy.MakeFeatureLayer_management (v_osm_transport, "temp_layer4") 

# BYM
v_bym_lekeplass_point = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Fritid\BYM_lekeplass_OB_2015.shp"
v_bym_svomme_point = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Idrettsanlegg\BYM_svommeanlegg_OB_2018.shp"
v_bym_stop_points = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\BYM\TEMADATA\Samferdsel\BYM_holdeplasser_trikk_buss_OK_2015.shp"

# Indre by
v_city = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\Hedonics\Xianwen_Chen\Inputs\Byggesone_innerOuterCity_25832.shp"
l_city = arcpy.MakeFeatureLayer_management(v_city, "l_city")

## functions
def EuclideanDistanceToFeature(v_feature, v_points, feature_type_name):
    r_distance = "temp_la_{}_raster".format(feature_type_name)
    a_distance = "la_{}".format(feature_type_name)
    
    # compute distance raster 
    arcpy.gp.EucDistance_sa(v_feature, r_distance, "", "2", "")
    
    # extract values at sales points
    ExtractRasterValuesToPoints(v_points, r_distance, a_distance)
    

def ExtractRasterValuesToPoints(v_points, r_values, a_name):
    v_point_values = "temp_point_values"
    
    # extract
    arcpy.gp.ExtractValuesToPoints_sa(v_points, r_values, v_point_values)

    # join values back to points
    AddFieldIfNotexists(v_points, a_name, "Double")
    join_and_copy(v_points, "JOIN_ID", v_point_values, "JOIN_ID", ["RASTERVALU"], ["{}".format(a_name)])
    arcpy.Delete_management(v_point_values)


# ====================================== #
# ===== Distance to nearest school ===== #
# ====================================== #
school_dict = {
    "barnehage": "612, 615",
    "barneskole": "613",
    "ungdomsskole": "614, 615",
    "vidergaende": "616",
    "universitetet": "621, 629"
}    
  
for schooltype in school_dict:
    arcpy.AddMessage("Computing {}...".format(schooltype))
    
    expression = "bygningstype IN ({})".format(school_dict[schooltype])  
    arcpy.SelectLayerByAttribute_management(l_fkb_buildings, "NEW_SELECTION", expression)
    EuclideanDistanceToFeature(l_fkb_buildings, v_sales_points_simple, schooltype)

    
# ========================================== # 
# ===== Distance to nearest playground ===== # 
# ========================================== #
arcpy.AddMessage ("Computing playground...")

# input data
arcpy.SelectLayerByAttribute_management(l_osm_poi_point, "NEW_SELECTION", "code = 2205")   
arcpy.SelectLayerByAttribute_management(l_osm_poi_area, "NEW_SELECTION", "code = 2205")

v_lekeplass_merge = "temp_la_lekeplass_merge"
arcpy.Merge_management ([l_osm_poi_point, v_bym_lekeplass_point], v_lekeplass_merge)

# compute distance raster separately for points and polygons
r_distance_point = "temp_la_lekeplass_raster_point"
r_distance_poly  = "temp_la_lekeplass_raster_poly"

arcpy.gp.EucDistance_sa(v_lekeplass_merge, r_distance_point, "", "2", "")
arcpy.gp.EucDistance_sa(l_osm_poi_area, r_distance_poly, "", "2", "")
arcpy.Delete_management(v_lekeplass_merge)

# take minimum of these rasters
r_distance = CellStatistics([r_distance_point, r_distance_poly], "MINIMUM", "NODATA")

# save the output 
r_distance.save(r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_la.gdb\temp_la_lekeplass_raster")
arcpy.Delete_management(r_distance_point)
arcpy.Delete_management(r_distance_poly)

# extract values at sales points
ExtractRasterValuesToPoints(v_sales_points_simple, "temp_la_lekeplass_raster", "la_lekeplass")


# ============================================= # 
# ===== Distance to nearest swimming pool ===== # 
# ============================================= # 
arcpy.AddMessage ("Computing swimming pool...")

# input data
arcpy.SelectLayerByAttribute_management(l_osm_poi_point, "NEW_SELECTION", "code = 2253")
arcpy.SelectLayerByAttribute_management(l_fkb_buildings, "NEW_SELECTION", "bygningstype = 653")

v_svomme_merge = arcpy.Merge_management ([l_osm_poi_point, v_bym_svomme_point], "temp_la_svomme_merge")

# compute distance raster separately for points and polygons
r_distance_point = "temp_la_svomme_raster_point"
r_distance_poly  = "temp_la_svomme_raster_poly"

arcpy.gp.EucDistance_sa(v_svomme_merge, r_distance_point, "", "2", "")
arcpy.gp.EucDistance_sa(l_fkb_buildings, r_distance_poly, "", "2", "")
arcpy.Delete_management(v_svomme_merge)

# take minimum of these rasters
r_distance = CellStatistics([r_distance_point, r_distance_poly], "MINIMUM", "NODATA")

# save the output 
r_distance.save(r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_la.gdb\temp_la_svomme_raster")
arcpy.Delete_management(r_distance_point)
arcpy.Delete_management(r_distance_poly)

# extract values at sales points
ExtractRasterValuesToPoints(v_sales_points_simple, "temp_la_svomme_raster", "la_svomme")


# =============================================== #  
# ===== Distance to nearest shopping center ===== #
# =============================================== #  
arcpy.AddMessage ("Computing shopping center...")

arcpy.SelectLayerByAttribute_management(l_fkb_buildings, "NEW_SELECTION", "bygningstype = 321")
EuclideanDistanceToFeature(l_fkb_buildings, v_sales_points_simple, "shop")


# ===================================================== # 
# ===== Distance to nearest public transport stop ===== #
# ===================================================== # 
arcpy.AddMessage ("Computing public transport...")

arcpy.SelectLayerByAttribute_management(l_osm_transport, "NEW_SELECTION", "code IN (5601, 5602, 5603, 5621, 5622, 5661)")

# merge point data
v_stop_merge = "temp_la_stop_merge"
arcpy.Merge_management ([l_osm_transport, v_bym_stop_points], "temp_la_stop_merge")

# compute distance raster
EuclideanDistanceToFeature(v_stop_merge, v_sales_points_simple, "stop")
arcpy.Delete_management(v_stop_merge)


# ==================== #
# ===== Indre by ===== #
# ==================== #    
arcpy.AddMessage ("Computing indre by...")

# extract indre by
arcpy.SelectLayerByAttribute_management (l_city, "NEW_SELECTION", "Byggesone = 'Inner'")
EuclideanDistanceToFeature(l_city, v_sales_points_simple, "city")

