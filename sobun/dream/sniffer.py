import re

from bluepy.btle import Scanner, DefaultDelegate

from dream.syncer import push

# from ScanEntry in https://ianharvey.github.io/bluepy-doc/index.html
# 
# data structure:
#   1. All BLE devices emit BLE advertising packets called bleAdvertisement
#   within the advertising packet is a description `desc` 
#   filter out devices with desc != manufacturer
#   2. Of the devices with desc == manufacturer, 
#   in the payload there's a device address `addr` and a `value`
#   the `addr` is the Tag ID (for fujitsu packets)
#   the `value` contains the manufacturer ID (for Fujistu 010003000300) 
#   and the measurement we care about (temperature & acceleration)
def extract_packet_payload(bleAdvertisement):
    try:
        # extract all packet data
        scan_data_hash = {}
        # tripple has the advertising type, description and value (adtype, desc, value) 
        tag_id = bleAdvertisement.addr.replace(':', '')
        triples = bleAdvertisement.getScanData()
        # filter only for advertisements where the description is Manufacturer
        # return a list, where the last element of the list is the payload value 
        values = [value for (adtype, desc, value) in triples if desc == 'Manufacturer']
        if len(values):
            return {
                "tag_id": tag_id,
                "measurements": values[-1],
            }
        return None

    except (UnicodeEncodeError, UnicodeDecodeError):
        # there's a bug where this error detector flags an unknown device for an unknown reason.
        # for now we're leaving it alone, but it might be important eventually
        # msg = "Failed to extract packet data from device %s" % bleAdvertisement.addr
        # print msg
        return None


FUJITSU_PACKET_REGEX = re.compile(r'010003000300')

def is_fujitsu_tag(payload):
    return re.search(FUJITSU_PACKET_REGEX, payload['measurements'])


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, bleAdvertisement, isNewTag, isNewData):
        payload = extract_packet_payload(bleAdvertisement)
        if payload:
            if is_fujitsu_tag(payload):
                push.delay(payload)


if __name__ == '__main__':
    handler = ScanDelegate()
    scanner = Scanner().withDelegate(handler)
    scanner.scan(11)