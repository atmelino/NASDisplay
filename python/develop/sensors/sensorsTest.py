import sensors
from pprint import pprint
sensors.init()
try:
    print 'sensors.iter_detected_chips() gives list mychips'
    mychips=sensors.iter_detected_chips()
    mychips1=sensors.iter_detected_chips()
    print 'mychips has %d items' % len(list(mychips1))

    for chip in mychips:
        print '%s at %s' % (chip, chip.adapter_name)
        pprint(chip)
        print 'chip has %d features' % len(list(chip))

        for feature in chip:
            print '  %s: %.2f' % (feature.label, feature.get_value())
finally:
    sensors.cleanup()
