import sensors

sensors.init()
try:
    for chip in sensors.iter_detected_chips():
        for feature in chip:
            label = feature.label.replace(' ', '-')
            value = None
            try:
                value = feature.get_value()
            except Exception:
                value = 0

            if value is not None:
                print '%s  %s: %.2f' % (chip,feature.label, value)
finally:
    sensors.cleanup()
