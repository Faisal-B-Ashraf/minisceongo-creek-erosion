# Lidar (not stored in the repository)

Download the two raw tiles (uncompressed LAS) from the NYS GIS Clearinghouse into any folder:

- https://gisdata.ny.gov/elevation/LIDAR/USGS_NorthEast2011/18_05854562.las (2011 survey, about 56 MB)
- https://gisdata.ny.gov/elevation/LIDAR/NYS_Southeast4County2022/u_5850056150_2022.las (2022 survey, about 365 MB)

Then run `python analysis/2_Scripts/04_lidar_south_bank.py <folder with the two .las files>`. It clips both surveys to
the study area (LiDAR_2011_Nov_points_clip.csv, LiDAR_2022_Apr_points_clip.csv) and builds the 1-ft ground surfaces
here (Ground_DEM_2011_Nov_1ft.tif, Ground_DEM_2022_Apr_1ft.tif). Later runs work from the clipped files.
