python ..\regionclipper.py --pathRegistry .\pathRegistry.json --regionClipperConfig .\regionClipperConfig.json --subRegionConfig .\subRegions.json --subRegionNames "Arrow,Boundary"
python ..\regiongridder.py --pathRegistry .\pathRegistry.json --regionGridderConfig .\regionGridderConfig.json --subRegionConfig .\subRegions.json --subRegionNames "Arrow,Boundary"
python ..\rollback.py --pathRegistry .\pathRegistry.json --rollbackConfig .\rollbackConfig.json --subRegionConfig .\subRegions.json --subRegionNames "Arrow,Boundary"
