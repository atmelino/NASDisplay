import sensors
from pprint import pprint
sensors.init()
try:
    for chip in sensors.iter_detected_chips():
        print '%s at %s' % (chip, chip.adapter_name)

        print(chip)
        print vars(chip)
        pprint(chip)

    if chip.has_key('feature')==1:
        for feature in chip:
            print '  %s: %.2f' % (feature.label, feature.get_value())
finally:
    sensors.cleanup()
