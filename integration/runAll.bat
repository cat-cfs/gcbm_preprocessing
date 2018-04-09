
python ..\preprocessorsetup.py --pathRegistry .\pathRegistry.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary" --spatial --aspatial --tools --future

python ..\regionclipper.py --pathRegistry .\pathRegistry.json --regionClipperConfig .\regionClipperConfig.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary"
python ..\regiongridder.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary"
python ..\rollback.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary"
python ..\historicprocessor.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json --subRegionConfig .\subRegionConfig.json --runtiler --subRegionNames "Boundary"
python ..\futureprocessor.py --pathRegistry .\pathRegistry.json --futureConfig .\futureConfig.json --subRegionConfig .\subRegionConfig.json --runtiler --subRegionNames "Boundary"
python ..\recliner2GCBM.py --pathRegistry .\pathRegistry.json --futureConfig .\futureConfig.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary" 
python ..\runupdategcbmconfig.py --pathRegistry .\pathRegistry.json --futureConfig .\futureConfig.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary" 