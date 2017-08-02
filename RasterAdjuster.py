#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  2 13:59:11 2017

@author: silent
"""

import gdal, ogr
import json

class RasterAdjuster():
    
    def __init__(self,raster1_path,raster2_path):
        
        # Read datasets
        self.raster1 = gdal.Open(raster1_path)
        self.raster2 = gdal.Open(raster2_path)
        
        # From GCP to projected
        if self.check_gcp_raster(self.raster1):
            self.raster1 = self.gcp_raster_to_projected(self.raster1)
        if self.check_gcp_raster(self.raster2):
            self.raster2 = self.gcp_raster_to_projected(self.raster2)
        
        # Reproject second dataset to projection of first dataset
        if self.raster1.GetProjection() != self.raster2.GetProjection():
            self.raster2 = self.reproject_raster_to_projection(self.raster2,raster1.GetProjection())
        
        # Get extents
        self.raster1_extent = self.extent_to_wkt_polygon(self.get_extent(self.raster1))
        self.raster2_extent = self.extent_to_wkt_polygon(self.get_extent(self.raster2))
        
        # Get intersection
        self.intersection = self.intersect_two_wkt_polygons(self.raster1_extent,self.raster2_extent)
        # TODO: if intersection is empty
        
        # cut raster1 to intersection
        self.raster1 = self.crop_raster_by_polygon_wkt(self.raster1,self.intersection)
        
        # project raster2 to current domain of raster1
        self.raster2 = self.project_raster_to_existing_raster_domain(self.raster2,self.raster1)
        
        
    def set_resolution(self,xRes,yRes):
        self.raster1 = gdal.Warp('',self.raster1,format='MEM',xRes=xRes,yRes=yRes)
        self.raster2 = gdal.Warp('',self.raster2,format='MEM',xRes=xRes,yRes=yRes)
    
    
    ##########    
        
        
    def reproject_raster_to_projection(self,raster,dest_projection):
        source_projection = self.get_projection(raster)
        output_raster = gdal.Warp('', raster, srcSRS=source_projection, dstSRS=dest_projection, format='MEM')
        return output_raster
    
    def get_projection(self,raster):
        return raster.GetProjection()
    
    def get_extent(self,raster):
        geoTransform = raster.GetGeoTransform()
        xMin = geoTransform[0]
        yMax = geoTransform[3]
        xMax = xMin + geoTransform[1] * raster.RasterXSize
        yMin = yMax + geoTransform[5] * raster.RasterYSize
        return {'xMax':xMax,'xMin':xMin,'yMax':yMax,'yMin':yMin}
    
    def extent_to_wkt_polygon(self,extent):
        return 'POLYGON ((%s %s,%s %s,%s %s,%s %s,%s %s))' % (extent['xMin'],extent['yMin'],extent['xMin'],extent['yMax'],
                                                                extent['xMax'],extent['yMax'],extent['xMax'],extent['yMin'],
                                                                extent['xMin'],extent['yMin'])
    
    
    
    def intersect_two_wkt_polygons(self,polygon_wkt1,polygon_wkt2):
        polygon1 = ogr.CreateGeometryFromWkt(polygon_wkt1)
        polygon2 = ogr.CreateGeometryFromWkt(polygon_wkt2)
        intersection = polygon1.Intersection(polygon2)
        return intersection.ExportToWkt()
    
    def check_gcp_raster(self,raster):
        if raster.GetGCPCount():
            return True
        else:
            return False
    
    def gcp_raster_to_projected(self,raster):
        output_raster = gdal.Warp('', raster, format='MEM')
        return output_raster
    
    def create_memory_ogr_datasource_with_wkt_polygon(self,polygon_wkt):
        drv = ogr.GetDriverByName('MEMORY') 
        source = drv.CreateDataSource('memData') 
        layer = source.CreateLayer('l1',geom_type=ogr.wkbPolygon)
        
        feature_defn = layer.GetLayerDefn()
        feature = ogr.Feature(feature_defn)
        geom = ogr.CreateGeometryFromWkt(polygon_wkt)
        feature.SetGeometry(geom)
        layer.CreateFeature(feature)
        layer.SyncToDisk()
        return source   
    
    def json_polygon_to_extent(self, polygon_json):
        x_list = []
        y_list = []
        for pair in json.loads(polygon_json)['coordinates']:
            x_list.append(pair[0])
            y_list.append(pair[1])
        return {'xMax':max(x_list),'xMin':min(x_list),'yMax':max(y_list),'yMin':min(y_list)}
    
    def crop_raster_by_polygon_wkt(self,raster,polygon_wkt):
        # TODO: find out memory ogr
        #cutline = self.create_memory_ogr_datasource_with_wkt_polygon(polygon_wkt)
        #output_raster = gdal.Warp('', raster, cropToCutline=True, cutlineLayer = cutline, format = 'MEM')
        #return output_raster
        # ---
        geom = ogr.CreateGeometryFromWkt(polygon_wkt)
        extent_json = geom.GetBoundary().ExportToJson()
        extent = self.json_polygon_to_extent(extent_json)
        output_raster = gdal.Warp('', raster, outputBounds = [extent['xMin'],extent['yMin'],extent['xMax'],extent['yMax']], format = 'MEM')
        return output_raster
    
    def project_raster_to_existing_raster_domain(self,raster,domain):
        extent = self.get_extent(domain)
        xSize = domain.RasterXSize
        ySize = domain.RasterYSize
        output_raster = gdal.Warp('',raster,outputBounds = [extent['xMin'],extent['yMin'],extent['xMax'],extent['yMax']],width=xSize, height=ySize, format='MEM')
        return output_raster
            
    def save_raster_to_gtiff(self,raster,gtiff_path):
        driver = gdal.GetDriverByName("GTiff")
        dataType = raster.GetRasterBand(1).DataType
        #dataType = gdal.GetDataTypeName(dataType)
        dataset = driver.Create(gtiff_path, raster.RasterXSize, raster.RasterYSize, raster.RasterCount, dataType)
        dataset.SetProjection(raster.GetProjection())
        dataset.SetGeoTransform(raster.GetGeoTransform())
        i = 1
        while i<= raster.RasterCount:
            dataset.GetRasterBand(i).WriteArray(raster.GetRasterBand(i).ReadAsArray())
            i+=1
        del dataset
