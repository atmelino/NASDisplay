import sensors
from pprint import pprint
sensors.init()
try:
    mychips = sensors.iter_detected_chips()
    numberOfChips = len(list(mychips))
    print 'computer has %d chips' % numberOfChips
    if numberOfChips > 0:
        for chip in mychips:
            print '%s ' % chip
            numberOfFeatures = len(list(chip))
            print 'chip %s has %d features' % (chip, numberOfFeatures)


    mychips = sensors.iter_detected_chips()
    if numberOfChips > 0:
        for chip in mychips:
            print '%s at %s' % (chip, chip.adapter_name)
            pprint(chip)
            numberOfFeatures = len(list(chip))
            print 'chip has %d features' % numberOfFeatures
            if numberOfFeatures > 0:
                for feature in chip:
                    print '  %s: %.2f' % (feature.label, feature.get_value())





finally:
    sensors.cleanup()
