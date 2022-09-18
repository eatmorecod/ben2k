from canlib import canlib
from canlib.canlib import ChannelData
import sys
from time import sleep

# Open a new channel, set bitrate 250Kbit/s and go bus on
def open_channel(channel):
    ch = canlib.openChannel(channel, canlib.canOPEN_ACCEPT_VIRTUAL)
    print(f'Using channel: {ChannelData(channel).channel_name}, EAN: {ChannelData(channel).card_upc_no}')
    ch.setBusOutputControl(canlib.canDRIVER_SILENT)
    ch.setBusParams(canlib.canBITRATE_250K)
    ch.busOn()
    if ChannelData(channel).card_upc_no == '00-00000-00000-0':
        ch = None
    return ch

    # Initialize CAN channel to receive position data
try:
    ch0 = open_channel(0) 
except:
    print("Unable to initialize CAN channel.")
    ch0 = None
    
# Read NMEA 2000 position data from CAN bus
def nmea2k(ch):
    ownship = {}
    var = False
    position = False
    hdg = False
    cog = False
    while True:
        try:
            frame = ch.read(timeout=500)
        except(canlib.canNoMsg) as ex:
            pass
        except(canlib.canError) as ex:
            print(ex)
        
        pgn = (frame.id & 33554176)>>8 # Decode pgn from message identifier
        data = []
            
        # Variation
        if pgn == 0x1F11A:
            for byte in frame.data:
                data.append(byte)
            var = f'{data[5]:02x}{data[4]:02x}'
            if int(var, 16) > 0x0fff:
                var = (int(var, 16) - 0xffff) * .0057
            
            
            
        # HEADING
        '''if pgn == 0x1F112:
            for byte in frame.data:
                data.append(byte)
     
            hdg = f'{data[2]:02x}{data[1]:02x}'
           
            if data[7] == 253:
      
                
                
                if var:
                    hdg = (int(hdg, 16) * .0057) + var
                    if hdg < 0:
                        hdg += 360
                    sys.stdout.write(f'HDG: {str(round(hdg, 1))}°T  \r')
                    sys.stdout.flush()
               
                


         
  
            hdg = True'''

        # COG/SOG
        if pgn == 0x1F802:
            for byte in frame.data:
                data.append(byte)
            cog = f'{data[3]:02x}{data[2]:02x}'
            ownship['cog'] = int(cog, 16) * .0057
            sog = f'{data[5]:02x}{data[4]:02x}'
            ownship['sog'] = int(sog, 16) * 1 * 10** -2        
            cog = True
       
        # POSITION
        if pgn == 0x1F801:
            for byte in frame.data:
                data.append(byte)
            lat = f'{data[3]:02x}{data[2]:02x}{data[1]:02x}{data[0]:02x}'
            lon = f'{data[7]:02x}{data[6]:02x}{data[5]:02x}{data[4]:02x}'
            ownship["lat"] = int(lat, 16) * 1 * 10** -7
            if int(lon, 16) > int(0x0fffffff):
                ownship['lon'] = (int(lon, 16) - int(0xffffffff)) * 1 * 10** -7
            else:
                ownship['lon'] = int(lon, 16) * 1 * 10** -7             
            position = True

        #XTE
        if pgn == 0x1F903:
            for byte in frame.data:
                data.append(byte)

            xte = f'{data[5]:02x}{data[4]:02x}{data[3]:02x}{data[2]:02x}'
            if int(xte, 16) > 0x0fffffff:
                xte = (int(xte, 16) - 0xffffffff) * 1 * 10** -2
            else:
                xte = int(xte, 16) * 1 * 10** -2
            sys.stdout.write(f'XTE: {str(round(xte, 2))}  \r')
            sys.stdout.flush()

        
        
while True:
    try:
        if ch0:
            ownship = nmea2k(ch0)
    except KeyboardInterrupt:
        break      