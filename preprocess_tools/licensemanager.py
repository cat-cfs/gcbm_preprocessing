import logging
import time
import os
from contextlib import contextmanager
from sshtunnel import SSHTunnelForwarder
from multiprocessing import Process

active_tunnel = False

# Fixes interaction between time and multiprocessing modules.
os.environ["FOR_DISABLE_CONSOLE_CTRL_HANDLER"] = "1"
os.environ["FOR_IGNORE_EXCEPTIONS"] = "1"

class Extensions(object):
    def __init__(self): raise RuntimeError("Not instantiable")

    GEOSTATS = "GeoStats"
    SPATIAL = "Spatial"
    
    @staticmethod
    def manages(name):
        return name in [Extensions.GEOSTATS, Extensions.SPATIAL]
        
    @staticmethod
    def checkout(extension):
        try:
            import archook
            archook.get_arcpy()
            import arcpy
            arcpy.CheckOutExtension(extension)
            return arcpy
        except Exception as e:
            logging.debug(e)
            return None
            
    @staticmethod
    def release(extension):
        try:
            arcpy.CheckInExtension(extension)
        except:
            pass

  
class Products(object):
    def __init__(self): raise RuntimeError("Not instantiable")

    ARC         = "Arc"
    ARCINFO     = "ArcInfo"
    ARCEDITOR   = "ArcEditor"
    ARCVIEW     = "ArcView"
    
    @staticmethod
    def manages(name):
        return name in [Products.ARC, Products.ARCINFO, Products.ARCEDITOR, Products.ARCVIEW]
        
    @staticmethod
    def checkout(name):
        try:
            if name == Products.ARCINFO:   import arcinfo
            if name == Products.ARCEDITOR: import arceditor
            if name == Products.ARCVIEW:   import arcview
            import archook
            archook.get_arcpy()
            import arcpy
            return arcpy if arcpy.ProductInfo() != "NotInitialized" else None
        except Exception as e:
            logging.debug(e)
            return None
    
    @staticmethod
    def release(name):
        try:
            if name == Products.ARCINFO:   del arcinfo
            if name == Products.ARCEDITOR: del arceditor
            if name == Products.ARCVIEW:   del arcview
            del arcpy
        except:
            pass

def start_tunnel(tunnel_conf):
    tunnel = SSHTunnelForwarder(
        (tunnel_conf["tunnel_host"], 22),
        ssh_username=tunnel_conf["tunnel_username"],
        ssh_password=tunnel_conf["tunnel_password"],
        remote_bind_addresses=[
            (tunnel_conf["license_host"], 27000),
            (tunnel_conf["license_host"], int(tunnel_conf["license_port"]))],
        local_bind_addresses=[
            ("localhost", 27000),
            ("localhost", int(tunnel_conf["license_port"]))],
        set_keepalive=60,
        mute_exceptions=True)
    tunnel.start()
    while True:
        time.sleep(30)
        tunnel.check_tunnels()
        all_tunnels_up = all(tunnel.tunnel_is_up)
        logging.debug("Tunnels up?: {}".format(all_tunnels_up))
        if not all_tunnels_up:
            logging.debug("Attempting to restart tunnels")
            tunnel.restart()

@contextmanager
def arc_license(product_or_extension):
    mgr = None
    for license_manager in (Products, Extensions):
        if license_manager.manages(product_or_extension):
            mgr = license_manager
    
    if not mgr:
        logging.fatal("Tried to acquire unsupported license: {}.".format(product_or_extension))
        return
    
    wait_time = 60
    max_retries = 60**2 * 48 / wait_time # Retry for up to 24 hours
    
    tunnel_conf_file = os.path.join(os.path.dirname(__file__), "arc_license_tunnel.conf")
    tunneled_license = os.path.exists(tunnel_conf_file)
    global active_tunnel
    if tunneled_license and not active_tunnel:
        active_tunnel = True
        tunnel_conf = dict((line.split() for line in open(tunnel_conf_file, "r")))
        tunnel_process = Process(target=start_tunnel, args=(tunnel_conf,))
        tunnel_process.daemon = True
        tunnel_process.start()
    
    attempt = 1
    try:
        license = None
        logging.debug("Acquiring {} license...".format(product_or_extension))
        while not license and attempt < max_retries:
            license = mgr.checkout(product_or_extension)
            if not license:
                attempt += 1
                logging.info("Waiting for {} license...".format(product_or_extension))
                try:
                    time.sleep(wait_time)
                except:
                    pass
        
        attempts = "{} attempt{}".format(attempt, "s" if attempt > 1 else "")
        if license:
            logging.info("Acquired {} license after {}.".format(product_or_extension, attempts))
        else:
            logging.fatal("Failed to acquire {} license after {}.".format(product_or_extension, attempts))
            
        yield license
    finally:
        logging.debug("Releasing {} license.".format(product_or_extension))
        mgr.release(product_or_extension)
