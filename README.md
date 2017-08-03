# RasterAdjuster
Based on gdal/ogr class for simple and fast adjusting georasters

Prerequisites: gdal>=2.1

Author: Eduard Kazakov (silenteddie@gmail.com)

Last modification: 2017-08-03

Usage example:

```python
# Initializate class, all work will be done immediately
adjuster = RasterAdjuster('raster1_path','raster2_path')

# For now you have two adjusted gdal raster datasets
# Note, that second raster is projected to domain of first raster
adjuster.raster1
adjuster.raster2

# You have some posibilities to modificate domain
# Set new resolution
adjuster.set_resolution(100,100)
# Reproject
adjuster.set_projection('epsg:3995')

# Export data as arrays
adjuster.get_raster1_as_array()
adjuster.get_raster2_as_array(band_number=1)

# Export data to geotiff, to the same directory as inputs
adjuster.export()

# Export data to geotiff, to the custom places
adjuster.export(raster1_export_path='/home/silent/r1.tif',raster1_export_path='/home/silent/r2.tif')
```
