from segment import Segment


# #################################################################################################################### #
# RDTLayer                                                                                                             #
#                                                                                                                      #
# Description:                                                                                                         #
# The reliable data transfer (RDT) layer is used as a communication layer to resolve issues over an unreliable         #
# channel.                                                                                                             #
#                                                                                                                      #
#                                                                                                                      #
# Notes:                                                                                                               #
# This file is meant to be changed.                                                                                    #
#                                                                                                                      #
#                                                                                                                      #
# #################################################################################################################### #


class RDTLayer(object):
    # ################################################################################################################ #
    # Class Scope Variables                                                                                            #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    DATA_LENGTH = 4 # in characters                     # The length of the string data that will be sent per packet...
    FLOW_CONTROL_WIN_SIZE = 15 # in characters          # Receive window size for flow-control
    sendChannel = None
    receiveChannel = None
    dataToSend = ''
    currentIteration = 0                                # Use this for segment 'timeouts'

    # ################################################################################################################ #
    # __init__()                                                                                                       #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def __init__(self):
        self.sendChannel = None
        self.receiveChannel = None
        self.dataToSend = ''
        self.currentIteration = 0
        self.seqnum = 0
        self.received = ''
        self.receiveBuff = []
        self.sendBuff = {}
        self.countSegmentTimeouts = 0
        self.unacked = 0

    # ################################################################################################################ #
    # setSendChannel()                                                                                                 #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to set the unreliable sending lower-layer channel                                                 #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def setSendChannel(self, channel):
        self.sendChannel = channel

    # ################################################################################################################ #
    # setReceiveChannel()                                                                                              #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to set the unreliable receiving lower-layer channel                                               #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def setReceiveChannel(self, channel):
        self.receiveChannel = channel

    # ################################################################################################################ #
    # setDataToSend()                                                                                                  #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to set the string data to send                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def setDataToSend(self,data):
        self.dataToSend = data

    # ################################################################################################################ #
    # getDataReceived()                                                                                                #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Called by main to get the currently received and buffered string data, in order                                  #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def getDataReceived(self):
        # ############################################################################################################ #
        # Identify the data that has been received...
        # ############################################################################################################ #
        return self.received

    # ################################################################################################################ #
    # processData()                                                                                                    #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # "timeslice". Called by main once per iteration                                                                   #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processData(self):
        self.currentIteration += 1
        self.processSend()
        self.processReceiveAndSendRespond()

    # ################################################################################################################ #
    # processSend()                                                                                                    #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Manages Segment sending tasks                                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processSend(self):

        # ############################################################################################################ #
        print('processSend(): ')
        if self.dataToSend:
            for i in range(RDTLayer.FLOW_CONTROL_WIN_SIZE//4):
                # Make sure the number of bytes that have been sent to server is always less than Flow Control Window Size
                if self.seqnum >= len(self.dataToSend) or (self.unacked * RDTLayer.DATA_LENGTH) > (RDTLayer.FLOW_CONTROL_WIN_SIZE - RDTLayer.DATA_LENGTH):
                    break
                self.unacked += 1
                segmentSend = Segment()
                seqnum = self.seqnum
                windowEnd = min(self.seqnum + RDTLayer.DATA_LENGTH, len(self.dataToSend))
                data = self.dataToSend[seqnum: windowEnd]
                seqnum += RDTLayer.DATA_LENGTH
                segmentSend.setData(seqnum, data)
                # Display sending segment
                print("Sending segment: ", segmentSend.to_string())

                # Use the unreliable sendChannel to send the segment
                self.sendChannel.send(segmentSend)
                self.seqnum += RDTLayer.DATA_LENGTH

                # Add segment to dictionary and set timer [timer, segment]
                self.sendBuff[seqnum] = [2, segmentSend]

    # ################################################################################################################ #
    # processReceive()                                                                                                 #
    #                                                                                                                  #
    # Description:                                                                                                     #
    # Manages Segment receive tasks                                                                                    #
    #                                                                                                                  #
    #                                                                                                                  #
    # ################################################################################################################ #
    def processReceiveAndSendRespond(self):

        # This call returns a list of incoming segments (see Segment class)...
        listIncomingSegments = self.receiveChannel.receive()
        for seg in listIncomingSegments:
            # drop packet if there is a checksum error
            if not seg.checkChecksum():
                print('Checksum error, packet dropped')
                continue

            # Server
            if seg.acknum == -1:
                segmentAck = Segment()  # Segment acknowledging packet(s) received
                expected = self.seqnum + RDTLayer.DATA_LENGTH
                # if not expected next segment, add to buffer
                if seg.seqnum != expected:
                    print("out of order")
                    # Check if the sequence number is in the receive buffer and is greater than current received to eliminate duplicates
                    if seg.seqnum not in [s[0] for s in self.receiveBuff] and seg.seqnum > self.seqnum:
                        self.receiveBuff.append((seg.seqnum, seg.payload))
                else:
                    self.received += seg.payload
                    self.seqnum = seg.seqnum
                acknum = seg.seqnum
                segmentAck.setAck(acknum)
                print("Sending ack: ", segmentAck.to_string())
                self.sendChannel.send(segmentAck)

            # Client
            else:
                print("Ack received: ", seg.acknum)
                if seg.acknum in self.sendBuff:
                    del self.sendBuff[seg.acknum]
                    self.unacked -= 1

        # fill what is possible
        if self.receiveBuff:
            print("Current Sequence: ", self.seqnum)
            self.buildData()

        #  count down and resend packet if lost:
        if self.sendBuff:
            for seg in self.sendBuff.keys():
                self.sendBuff[seg][0] -= 1
                time, segment = self.sendBuff[seg]

                # create new segment and retransmit. New segment needed in case of checksum errors.
                if time == 0:
                    begin = seg - RDTLayer.DATA_LENGTH
                    segmentSend = Segment()
                    windowEnd = seg
                    data = self.dataToSend[begin:windowEnd]
                    segmentSend.setData(seg, data)
                    self.sendChannel.send(segmentSend)
                    self.sendBuff[seg] = [3, segmentSend]
                    self.countSegmentTimeouts += 1

    def buildData(self) -> None:
        """
        Takes the receiving buffer current buffer of out of order or missing
        segments and fills and rebuilds what is possible. Returns None.
        """
        self.receiveBuff.sort()
        next = self.seqnum + RDTLayer.DATA_LENGTH
        processed = 0
        for data in self.receiveBuff:
            if data[0] == next:
                # print("--------------Expected: ", next)
                self.received += data[1]
                self.seqnum = next
                next += RDTLayer.DATA_LENGTH
                processed += 1
            else:
                continue
        for i in range(processed):
            del self.receiveBuff[0]
