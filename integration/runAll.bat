:: python ..\preprocessorsetup.py --pathRegistry .\pathRegistry.json
python ..\regionclipper.py --pathRegistry .\pathRegistry.json --regionClipperConfig .\regionClipperConfig.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary"
python ..\regiongridder.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary"
python ..\rollback.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary"
python ..\historicprocessor.py --pathRegistry .\pathRegistry.json --preprocessorConfig .\preprocessorConfig.json --subRegionConfig .\subRegionConfig.json --subRegionNames "Boundary"