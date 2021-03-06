python ..\preprocessorsetup.py --pathRegistry .\pathRegistry.json --subRegionConfig .\subRegionConfig.json --spatial --aspatial --tools --future --postgis
python ..\regionclipper.py --pathRegistry .\pathRegistry.json --regionClipperConfig .\regionClipperConfig.json --subRegionConfig .\subRegionConfig.json
python ..\regiongridder.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json --subRegionConfig .\subRegionConfig.json
python ..\rollback.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json --subRegionConfig .\subRegionConfig.json
python ..\historicprocessor.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json --subRegionConfig .\subRegionConfig.json
python ..\futureprocessor.py --pathRegistry .\pathRegistry.json --futureConfig .\futureConfig.json --subRegionConfig .\subRegionConfig.json
python ..\gcbminput.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json  --futureConfig .\futureConfig.json --subRegionConfig .\subRegionConfig.json --tiler --recliner2gcbm --gcbmconfig
python ..\rungcbm.py --pathRegistry .\pathRegistry.json --futureConfig .\futureConfig.json --subRegionConfig .\subRegionConfig.json