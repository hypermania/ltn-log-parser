# Parse a factorio debug file into a tsv file formatted as follows:
# T_1 T_2 T_3 T_4 T_5 T_6 DepotName DepotID ProviderName ProviderID RequesterName RequesterID TrainName TrainID Item Quantity Stack

# T_1: time the train left depot
# T_2: time the train arrived at provider
# T_3: time the train left provider
# T_4: time the train arrived at requester
# T_5: time the train left requester
# T_6: time the train arrived at depot


import numpy as np
import re

"""
sample1 = ' 599.421 Script @__LogisticTrainNetwork__/control.lua:1405: Creating Delivery: 320 stacks, Chralex >> Frankenfrank\n'
sample2 = ' 599.421 Script @__LogisticTrainNetwork__/control.lua:1418:   item,plastic-bar, 32000 in 320 stacks \n'
sample3 = '1162.049 Script @__LogisticTrainNetwork__/control.lua:533: Train [888] nil left LTN-stop [261632] Depot-001\n'
sample4 = '1165.413 Script @__LogisticTrainNetwork__/control.lua:382: Train [1389] Craig Samson arrived at LTN-stop [778640] Depot-015\n'
sample5 = ' 544.657 Script @__LogisticTrainNetwork__/control.lua:1320: created new order 0xE1 >> Wermatswil: 64271 item,processing-unit in 322/322 stacks, min length: 0 max length: 0\n'
sample6 = ' 547.693 Script @__LogisticTrainNetwork__/control.lua:1195: (getFreeTrain) largest available train Diabolical Demons {0xffffffff}, length: 0<=6<=0, inventory size: 320/326, distance: 172036\n'
sample7 = ' 599.419 Script @__LogisticTrainNetwork__/control.lua:1174: checking train Diabolical Demons ,force player/player, network 0xffffffff/0xffffffff, length: 0<=6<=0, inventory size: 320/643, distance: 154900\n'


match2 = creatingDelivery2.match(sample2)
match3 = trainLeaves.match(sample3)
match4 = trainArrives.match(sample4)
match5 = createdNewOrder.match(sample5)
match6 = getFreeTrain.match(sample6)
match7 = checkingTrain.match(sample7)
"""


creatingDelivery1 = re.compile(r'\s*(\d+\.\d*).+Creating\sDelivery:\s(\d+)\sstacks,\s(.+)\s>>\s(.+)\n')
creatingDelivery2 = re.compile(r'\s*(\d+\.\d*).+\s\s(.+),\s(.+)\sin\s(.+)\sstacks\s\n')
trainLeaves = re.compile(r'\s*(\d+\.\d*).+Train\s\[(\d+)\]\s.+\sleft\sLTN-stop\s\[(\d+)\]\s(.+)\n')
trainArrives = re.compile(r'\s*(\d+\.\d*).+Train\s\[(\d+)\]\s(.+)\sarrived\sat\sLTN-stop\s\[(\d+)\]\s(.+)\n')
createdNewOrder = re.compile(r'\s*(\d+\.\d*).+created\snew\sorder\s(.+)\s>>\s(.+):\s(\d+)\s(.+)\sin\s(\d+)/(\d+)\sstacks,\smin\slength:\s\d+\smax\slength:\s\d+\n')
getFreeTrain = re.compile(r'\s*(\d+\.\d*).+\(getFreeTrain\)\slargest\savailable\strain\s(.+)\s\{.+\},\slength:\s\d+<=\d+<=\d+,\sinventory\ssize:\s(\d+)/(\d+),\sdistance:\s(\d+)\n')
checkingTrain = re.compile(r'\s*(\d+\.\d*).+checking\strain\s(.+)\s,force\s.+/.+,\snetwork\s.+/.+,\slength:\s\d+<=\d+<=\d+,\sinventory\ssize:\s\d+/\d+,\sdistance:\s\d+\n')
foundTrain = re.compile(r'\s*(\d+\.\d*).+\(getFreeTrain\)\sfound\strain\s(.+)\s\{.+\},\slength:\s\d+<=\d+<=\d+,\sinventory\ssize:\s\d+/\d+,\sdistance:\s\d+\n')
trainToTransport = re.compile(r'\s*(\d+\.\d*).+Train')

deliveries = []
trainEvents = {}
trainNameIDMap = {}
stationNameIDMap = {}

filename = '/media/hypermania/Drive_001/factorio-current.cropped.log'
#filename = './factorio-current.cropped100000.log'

with open(filename) as fp:
    while True:
        line = fp.readline()
        if not line:
            break
        if createdNewOrder.match(line):
            while True:
                tempLine = fp.readline()
                if checkingTrain.match(tempLine):
                    continue
                if getFreeTrain.match(tempLine):
                    freeTrain = getFreeTrain.match(tempLine).group(2)
                    continue
                if foundTrain.match(tempLine):
                    freeTrain = foundTrain.match(tempLine).group(2)
                    continue
                break
            creatingDeliveryLine1 = fp.readline()
            creatingDeliveryLine2 = fp.readline()
            match1 = creatingDelivery1.match(creatingDeliveryLine1)
            match2 = creatingDelivery2.match(creatingDeliveryLine2)

            if not match1:
                print(creatingDeliveryLine1)
            
            time = float(createdNewOrder.match(line).group(1))
            trainName = freeTrain
            providerName = match1.group(3)
            requesterName = match1.group(4)
            itemName = match2.group(2)
            itemQuantity = int(match2.group(3))
            itemStack = int(match2.group(4))
            
            deliveries.append([time, trainName,
                               providerName, requesterName,
                               itemName, itemQuantity, itemStack])
            
        if trainLeaves.match(line):
            match = trainLeaves.match(line)
            eventTime = float(match.group(1))
            trainID = int(match.group(2))
            stationID = int(match.group(3))
            stationName = match.group(4)
            if trainID not in trainEvents:
                trainEvents[trainID] = []
            trainEvents[trainID].append((eventTime, 'leave', stationID))
            if stationID not in stationNameIDMap:
                stationNameIDMap[stationName] = stationID

        if trainArrives.match(line):
            match = trainArrives.match(line)
            eventTime = float(match.group(1))
            trainID = int(match.group(2))
            trainName = match.group(3)
            stationID = int(match.group(4))
            stationName = match.group(5)
            if trainID not in trainEvents:
                trainEvents[trainID] = []
            trainEvents[trainID].append((eventTime, 'arrive', stationID))
            if stationID not in stationNameIDMap:
                stationNameIDMap[stationName] = stationID
            if trainID not in trainNameIDMap:
                trainNameIDMap[trainName] = trainID

stationIDNameMap = {}
for key in stationNameIDMap:
    stationIDNameMap[stationNameIDMap[key]] = key

import sys

class ConsistencyError(Exception):
    pass
    
result = []
for delivery in deliveries:
    try:
        startTime = delivery[0]
        trainName = delivery[1]
        trainID = trainNameIDMap[delivery[1]]
        providerName = delivery[2]
        providerID = stationNameIDMap[delivery[2]]
        requesterName = delivery[3]
        requesterID = stationNameIDMap[delivery[3]]
        item = delivery[4]
        quantity = delivery[5]
        stack = delivery[6]

        events = [event for event in trainEvents[trainID] if event[0] > startTime][0:6]
        T1 = events[0][0]
        T2 = events[1][0]
        T3 = events[2][0]
        T4 = events[3][0]
        T5 = events[4][0]
        T6 = events[5][0]

        if events[0][1] != 'leave' or events[2][1] != 'leave' or events[4][1] != 'leave':
            print('Error 1')
            raise ConsistencyError
        if events[1][1] != 'arrive' or events[3][1] != 'arrive' or events[5][1] != 'arrive':
            print('Error 2')
            raise ConsistencyError
        if events[0][2] != events[5][2] or events[1][2] != events[2][2] or events[3][2] != events[4][2]:
            print('Error 3')
            raise ConsistencyError
        if events[1][2] != providerID or events[3][2] != requesterID:
            print('Error 4')
            raise ConsistencyError

        result.append((T1, T2, T3, T4, T5, T6,
                       stationIDNameMap[events[0][2]], events[0][2],
                       providerName, stationNameIDMap[providerName],
                       requesterName, stationNameIDMap[requesterName],
                       trainName, trainNameIDMap[trainName],
                       item, quantity, stack))

    except ConsistencyError:
        print('ConsistencyError')
        continue
        
    except:
        print('Exception')
        continue


outputFile = open('data.tsv', 'w')
for event in result:
    line = '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(*event)
    outputFile.write(line)
