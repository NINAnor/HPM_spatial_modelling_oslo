"""
NAME:    Computation of attributes for hedonic pricing model
         Green structure - neighbourhood

AUTHOR(S): Zofie Cimburova < zofie.cimburova AT nina.no>
"""

"""
To Dos: 
"""

import arcpy
import math  
import time
from arcpy import env
from arcpy.sa import *
from helpful_functions import *
  
## workspace settings
env.overwriteOutput = True
env.outputCoordinateSystem = arcpy.SpatialReference("ETRS 1989 UTM Zone 33N")
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OK_oslo_kommune_500m.shp"
env.cellSize = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\SENTINEL\s2_lc_OAF_08_2017_10m_25833.tif"
env.snapRaster = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\SENTINEL\s2_lc_OAF_08_2017_10m_25833.tif"
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_nbr.gdb"
   
   
## Functions
def ExtractRasterValuesToPoints(v_points, r_values, a_name):
    v_point_values = "temp_point_values"
    
    # extract
    arcpy.gp.ExtractValuesToPoints_sa(v_points, r_values, v_point_values)

    # join values back to points
    AddFieldIfNotexists(v_points, a_name, "Double")
    join_and_copy(v_points, "JOIN_ID", v_point_values, "JOIN_ID", ["RASTERVALU"], ["{}".format(a_name)])
    arcpy.Delete_management(v_point_values)


## input data
# sales points
v_sales_points_simple = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\input_data.gdb\sales_points_simple"

# Sentinel-2 NDVI
r_ndvi_s2 = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\SENTINEL\sentinel.gdb\s2_ndvi_OAF_08_2015_10m_25833"

# Sentinel-2 landcover
r_lc_s2 = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\SENTINEL\sentinel.gdb\s2_lc_OAF_08_2015_10m_25833"

# ALS tree canopy
v_tree_als_2011 = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\TREES\treedata.gdb\NINA_trees_OB_2011_polygons"
v_tree_als_2014 = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\TREES\treedata.gdb\NINA_trees_OB_2014_polygons"

# OB
v_ob = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OB_oslo_byggesonen.shp"

# Neighbourhood buffers
v_buff_clip = "temp_buff_clip"


## Prepare data
# sales points
l_sales_points_simple = arcpy.MakeFeatureLayer_management (v_sales_points_simple, "l_sales_points_simple")

AddFieldIfNotexists(v_sales_points_simple, "gs_nbr_green_ndvi", "Double")
AddFieldIfNotexists(v_sales_points_simple, "gs_nbr_green_s2", "Double")
AddFieldIfNotexists(v_sales_points_simple, "gs_nbr_tree_li_2011", "Double")
AddFieldIfNotexists(v_sales_points_simple, "gs_nbr_tree_li_2014", "Double")
AddFieldIfNotexists(v_sales_points_simple, "gs_nbr_lcd", "Double")

# Sentinel-2 NDVI reclass (NDVI < 0 -> NULL)
r_ndvi_s2_reclass = "s2_ndvi_reclass_OAF_08_2015_10m_25833"

# Sentinel-2 green classes (1,2,4 -> 1; 3,5 -> 0)
r_lc_s2_reclass = "s2_lc_reclass_OAF_08_2015_10m_25833"
arcpy.gp.Reclassify_sa(r_lc_s2, "VALUE", "1 1;2 1;3 0;4 1;5 0", r_lc_s2_reclass, "DATA")

# ALS trees
AddFieldIfNotexists(v_tree_als_2011, "Intersect_Area", "Double")
AddFieldIfNotexists(v_tree_als_2014, "Intersect_Area", "Double")

arcpy.CalculateField_management(v_tree_als_2011, "Intersect_Area", "!Shape!.area", "PYTHON_9.3")
arcpy.CalculateField_management(v_tree_als_2014, "Intersect_Area", "!Shape!.area", "PYTHON_9.3")

l_tree_als_2011 = arcpy.MakeFeatureLayer_management(v_tree_als_2011, "l_tree_als_2011")
l_tree_als_2014 = arcpy.MakeFeatureLayer_management(v_tree_als_2014, "l_tree_als_2014")

# buffers
l_buff_clip = arcpy.MakeFeatureLayer_management(v_buff_clip, "l_buff_clip")

# ================================== #
# ===== Average reclassed NDVI ===== #
# ================================== #  
r_stats_ndvi_s2 = "stats_ndvi_s2_500m"
arcpy.gp.FocalStatistics_sa(r_ndvi_s2_reclass, r_stats_ndvi_s2, "Circle 500 MAP", "MEAN", "DATA")
ExtractRasterValuesToPoints(v_sales_points_simple, r_stats_ndvi_s2, "gs_nbr_green_ndvi")


# ================================================ #
# ===== Percentage of grass+tree+agriculture ===== #
# ================================================ #
r_stats_lc_s2 = "stats_lc_s2_500m"
arcpy.gp.FocalStatistics_sa(r_lc_s2_reclass, r_stats_lc_s2, "Circle 500 MAP", "MEAN", "DATA")
ExtractRasterValuesToPoints(v_sales_points_simple, r_stats_lc_s2, "gs_nbr_green_s2")


# ===================================== #
# ===== Percentage of tree canopy ===== #
# ===================================== #
 cursor = arcpy.da.UpdateCursor(v_sales_points_simple, ['SHAPE@', 'JOIN_ID', 'gs_nbr_tree_li_2011', 'gs_nbr_tree_li_2014'])
 env.workspace = r"in_memory"

 for row in cursor:
    if row[1] >=200: # 10 pt 5.25 min
        
        arcpy.AddMessage ("Processing point {}.".format(row[1]))

        # 1. select trees within 500 m
        arcpy.SelectLayerByLocation_management (l_tree_als_2011, "WITHIN_A_DISTANCE", row[0], "500 meters", "NEW_SELECTION")
        arcpy.SelectLayerByLocation_management (l_tree_als_2014, "WITHIN_A_DISTANCE", row[0], "500 meters", "NEW_SELECTION")
        
        # 2. select corresponding buffer
        arcpy.SelectLayerByAttribute_management(l_buff_clip, "NEW_SELECTION", "JOIN_ID={}".format(row[1]))
        
        # 3. get buffer size
        a_nbr = 0
        cursorB = arcpy.da.SearchCursor(l_buff_clip, ["Buff_Area"])
        for rowB in cursorB:
            a_nbr = rowB[0]
        del(cursorB)
        
        # 4. summarize selected trees
        cnt2011 = int(arcpy.GetCount_management(l_tree_als_2011)[0])
        if cnt2011 > 0:     
            t_summary_trees_2011 = "temp_summary_trees_2011"
            arcpy.Statistics_analysis (l_tree_als_2011, t_summary_trees_2011, [["Intersect_Area", "SUM"]], "")         
      
            # update row        
            cursor2 = arcpy.da.SearchCursor(t_summary_trees_2011, ["SUM_Intersect_Area"])
            for row2 in cursor2:
                row[2] = row2[0] / a_nbr
                cursor.updateRow(row)   
            del(cursor2)
            arcpy.Delete_management(t_summary_trees_2011)
                    
        else:
            row[2] = 0
            cursor.updateRow(row)

        cnt2014 = int(arcpy.GetCount_management(l_tree_als_2014)[0])
        if cnt2014 > 0:     
            # summarize trees in neighbourhood
            t_summary_trees_2014 = "temp_summary_trees_2014"
            arcpy.Statistics_analysis (l_tree_als_2014, t_summary_trees_2014, [["Intersect_Area", "SUM"]], "")   
                    
            # update row        
            cursor3 = arcpy.da.SearchCursor(t_summary_trees_2014, ["SUM_Intersect_Area"])
            for row3 in cursor3:
                row[3] = row3[0] / a_nbr
                cursor.updateRow(row)   
            del(cursor3)
            arcpy.Delete_management(t_summary_trees_2014)
            
        else:
            row[3] = 0
            cursor.updateRow(row)
       
    


# =============================== #
# ===== Landcover diversity ===== #
# =============================== #
r_stats_diversity_s2 = "stats_diversity_s2_500m"
arcpy.gp.FocalStatistics_sa(r_lc_s2, r_stats_lc_s2, "Circle 500 MAP", "VARIETY", "DATA")
ExtractRasterValuesToPoints(v_sales_points_simple, r_stats_diversity_s2, "gs_nbr_lcd")

    
    
    
    
    
    
    
    
    
    
    
    
    
    