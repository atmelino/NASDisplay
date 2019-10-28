#!/usr/bin/env python

import sensors

def print_feature(chip, feature):
    #sfs = list(sensors.SubFeatureIterator(chip, feature)) # get a list of all subfeatures
    
    myLabel = feature.label
    myvalue=feature.get_value()
    

    print myLabel
    print myvalue

    #skipname = len(feature.name)+1 # skip common prefix
    #vals = [sensors.get_value(chip, sf.number) for sf in sfs]
    
    #if feature.type == sensors.feature.INTRUSION:
        # short path for INTRUSION to demonstrate type usage
        #status = "alarm" if int(vals[0]) == 1 else "normal"
        #print("\t"+label+"\t"+status)
        #Sreturn
    
    #names = [sf.name[skipname:].decode("utf-8") for sf in sfs]
    #data = list(zip(names, vals))
    
    #str_data = ", ".join([e[0]+": "+str(e[1]) for e in data])
    #print("\t"+label+"\t"+str_data)

if __name__ == "__main__":
    sensors.init() # optionally takes config file
    
    #print("libsensors version: "+sensors.version)
    
    for chip in sensors.iter_detected_chips(): # optional arg like "coretemp-*" restricts iterator
	print '%s at %s' % (chip, chip.adapter_name)
        for feature in chip:
            print_feature(chip, feature)
        
    sensors.cleanup()
