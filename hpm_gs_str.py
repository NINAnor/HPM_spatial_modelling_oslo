"""
NAME:    Computation of attributes for hedonic pricing model
         Green structure - street segment

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
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_str.gdb"
   
## input data
# sales points
v_sales_points_simple = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\input_data.gdb\sales_points_simple"

AddFieldIfNotexists(v_sales_points_simple, "gs_str_tree_s2", "Double")
AddFieldIfNotexists(v_sales_points_simple, "gs_str_tree_li", "Double")
AddFieldIfNotexists(v_sales_points_simple, "gs_str_gvi", "Double")

# Sentinel-2 trees
v_lc_s2 = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\LANDCOVER_LANDUSE\SENTINEL\sentinel.gdb\s2_lc_OAF_08_2017_10m_vector"
v_trees_s2 = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data_gs_str.gdb\temp_gs_s2_trees_OK_08_2017_10m"
arcpy.FeatureClassToFeatureClass_conversion(v_lc_s2, r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data.gdb", v_trees_s2, "gridcode = 4")

# LiDAR trees
v_trees_li = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\TREES\treedata.gdb\NINA_trees_OB_2017_polygons"

# GVI
v_gvi = r"R:\Prosjekter\15883000 - URBAN EEA\GIS\GreenViewIndex\Oslo_GVI\output_oslo_25832.shp"

# segment map
v_segment_map = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\TRANSPORT\data.gdb\segment_map_oslo"
l_segment_map = arcpy.MakeFeatureLayer_management (v_segment_map, "temp_segment_map_layer")


# ====================================== #
# ===== % tree cover in 10m buffer ===== #
# ====================================== #

# find nearest line
arcpy.AddMessage("Computing closest lines...")
v_sp_join = "temp_gs_1_sp_join"
arcpy.SpatialJoin_analysis(target_features=v_sales_points_simple, join_features=v_segment_map, out_feature_class=v_sp_join, join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL", field_mapping='', match_option="CLOSEST", search_radius="", distance_field_name="dist_axln")

# add field to store proportion of trees
AddFieldIfNotexists(v_sp_join, "gs_str_tree_s2", "Double")
AddFieldIfNotexists(v_sp_join, "gs_str_tree_li", "Double")
AddFieldIfNotexists(v_sp_join, "gs_str_gvi", "Double")


# go through sales points
cursor = arcpy.da.UpdateCursor(v_sp_join, ['SHAPE@', 'JOIN_ID', 'dist_axln', 'ID', 'gs_str_tree_s2', 'gs_str_tree_li', 'gs_str_gvi'])
env.workspace = r"in_memory"

for row in cursor:
    point_dist  = row[2] # distance to axial line
    line_id     = int(row[3]) # ID of closest axial line
    
    if row[1] > 1500 and row[1] <= 2500:
        arcpy.AddMessage("point {}, line {}".format(row[1], line_id))

        # compute buffer around point
        buffer_radius = math.sqrt(point_dist*point_dist + 90*90)
        v_buffer = "temp_gs_2_buff"
        arcpy.Buffer_analysis(row[0], v_buffer, "{} meters".format(buffer_radius))
        
        # select axial line belonging to point
        arcpy.SelectLayerByAttribute_management(l_segment_map, "NEW_SELECTION", "ID = {}".format(line_id))
      
        # clip axial line with buffer
        v_clip = "temp_gs_3_axial"
        arcpy.Clip_analysis(l_segment_map, v_buffer, v_clip)

        # check if there is an existing street - if not, <null>
        cnt = int(arcpy.GetCount_management(v_clip)[0])
        
        if cnt > 0:       
            # create buffer of line
            v_buffer = "temp_gs_4_axial_buff"
            arcpy.Buffer_analysis(v_clip, v_buffer, "10 Meters")
            arcpy.Delete_management(v_clip)
            
            env.extent = v_buffer
            
            add field to store area of buffer
            AddFieldIfNotexists(v_buffer, "Buff_area", "Double")
            arcpy.CalculateField_management(v_buffer, "Buff_area", "!Shape!.area", "PYTHON_9.3")
            
            clip forest pixels with buffer
            v_intersect_trees_s2 = "temp_gs_5_trees1_intersect"
            arcpy.Intersect_analysis([v_trees_s2, v_buffer], v_intersect_trees_s2)
            
            v_intersect_trees_li = "temp_gs_5_trees2_intersect"
            arcpy.Intersect_analysis([v_trees_li, v_buffer], v_intersect_trees_li)
            arcpy.Delete_management(v_buffer)
            
            v_intersect_gvi = "temp_gs_5_gvi_intersect"
            arcpy.Intersect_analysis([v_gvi, v_buffer], v_intersect_gvi)
            arcpy.Delete_management(v_buffer)
            
            # check if intersection is empty
            cnt2 = int(arcpy.GetCount_management(v_intersect_trees_s2)[0])
            if cnt2 > 0:
                # add field to store area
                AddFieldIfNotexists(v_intersect_trees_s2, "Tree_area", "Double")
                arcpy.CalculateField_management(v_intersect_trees_s2, "Tree_area", "!Shape!.area", "PYTHON_9.3")
                
                # summarize area of trees
                t_summary_s2 = "temp_gs_6_summary1"
                arcpy.Statistics_analysis(v_intersect_trees_s2, t_summary_s2, "Tree_area SUM;Buff_area FIRST", "ID_1")
                arcpy.Delete_management(v_intersect_trees_s2)
                
                # compute proportion of area
                AddFieldIfNotexists(t_summary_s2, "gs_str_tree_s2", "Double")
                arcpy.CalculateField_management(t_summary_s2, "gs_str_tree_s2", "[SUM_Tree_area]/[FIRST_Buff_area]")
            
                # copy to table
                cursor2 = arcpy.da.SearchCursor(t_summary_s2, ["gs_str_tree_s2"])
                for row2 in cursor2:
                    row[4] = row2[0]
                    cursor.updateRow(row)
                del(row2)
                del(cursor2)
                arcpy.Delete_management(t_summary_s2)
                
            else:
                row[4] = 0
                cursor.updateRow(row)
                arcpy.Delete_management(v_intersect_trees_s2)
            
            # check if intersection is empty
            cnt3 = int(arcpy.GetCount_management(v_intersect_trees_li)[0])
            if cnt3 > 0:
                AddFieldIfNotexists(v_intersect_trees_li, "Tree_area", "Double")       
                arcpy.CalculateField_management(v_intersect_trees_li, "Tree_area", "!Shape!.area", "PYTHON_9.3")
                       
                t_summary_li = "temp_gs_6_summary2"       
                arcpy.Statistics_analysis(v_intersect_trees_li, t_summary_li, "Tree_area SUM;Buff_area FIRST", "ID")
                arcpy.Delete_management(v_intersect_trees_li)
                
                AddFieldIfNotexists(t_summary_li, "gs_str_tree_li", "Double") 
                arcpy.CalculateField_management(t_summary_li, "gs_str_tree_li", "[SUM_Tree_area]/[FIRST_Buff_area]")

                cursor3 = arcpy.da.SearchCursor(t_summary_li, ["gs_str_tree_li"])
                for row3 in cursor3:
                    row[5] = row3[0]
                    cursor.updateRow(row)   
                del(row3)
                del(cursor3)
                arcpy.Delete_management(t_summary_li)
                
            else:
                row[5] = 0
                cursor.updateRow(row)
                arcpy.Delete_management(v_intersect_trees_li)
                
            # check if intersection is empty
            cnt4 = int(arcpy.GetCount_management(v_intersect_gvi)[0])
            if cnt4 > 0:                     
                t_summary_gvi = "temp_gs_6_summary3"       
                arcpy.Statistics_analysis(v_intersect_gvi, t_summary_gvi, "greenView MEAN", "ID")
                arcpy.Delete_management(v_intersect_gvi)

                cursor4 = arcpy.da.SearchCursor(t_summary_gvi, ["MEAN_greenView"])
                for row4 in cursor4:
                    row[6] = row4[0]
                    cursor.updateRow(row)   
                del(row4)
                del(cursor4)
                arcpy.Delete_management(t_summary_gvi)
                
            else:
                row[6] = 0
                cursor.updateRow(row)
                arcpy.Delete_management(v_intersect_gvi)
                
        else:
            arcpy.AddMessage("No axial line found")
            arcpy.Delete_management(v_buffer)
            arcpy.Delete_management(v_clip)
           
        env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OK_oslo_kommune.shp"

del row        
del cursor

    
env.extent = r"C:\Users\zofie.cimburova\OneDrive - NINA\GENERAL_DATA\EXTENT\OK_oslo_kommune.shp"
env.workspace = r"C:\Users\zofie.cimburova\OneDrive - NINA\URBAN_EEA\HPM VARIABLES\DATA\data.gdb"



