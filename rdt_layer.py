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
    # Add items as needed

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
        # Add items as needed

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

        print('getDataReceived():', self.received)

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

        # You should pipeline segments to fit the flow-control window
        # The flow-control window is the constant RDTLayer.FLOW_CONTROL_WIN_SIZE
        # The maximum data that you can send in a segment is RDTLayer.DATA_LENGTH
        # These constants are given in # characters

        # Somewhere in here you will be creating data segments to send.
        # The data is just part of the entire string that you are trying to send.
        # The seqnum is the sequence number for the segment (in character number, not bytes)
        if self.dataToSend:
            for i in range(RDTLayer.FLOW_CONTROL_WIN_SIZE//4):
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
                self.sendBuff[seqnum] = [5, segmentSend]

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
            if seg.acknum == -1:
                segmentAck = Segment()  # Segment acknowledging packet(s) received
                print('Segment received: ', seg.printToConsole())

                # if not expected next segment, add to buffer
                expected = self.seqnum + RDTLayer.DATA_LENGTH
                if seg.seqnum != expected:
                    print("out of order")
                    if seg.seqnum not in [s[0] for s in self.receiveBuff] and seg.seqnum > expected:
                        self.receiveBuff.append((seg.seqnum, seg.payload))
                else:
                    self.received += seg.payload
                    self.seqnum = seg.seqnum
                acknum = seg.seqnum
                segmentAck.setAck(acknum)
                print("Sending ack: ", segmentAck.to_string())
                self.sendChannel.send(segmentAck)
            else:
                print("Ack received: ", seg.acknum)
                if seg.acknum in self.sendBuff:
                    del self.sendBuff[seg.acknum]

        # fill what is possible
        if self.receiveBuff:
            print("Current Sequence: ", self.seqnum)
            self.buildData()

        #  count down and resend packet if lost:
        if self.sendBuff:
            for seg in self.sendBuff:
                self.sendBuff[seg][0] -= 1
                time, segment = self.sendBuff[seg]
                if time == 0:
                    self.sendChannel.send(segment)
                    self.sendBuff[seg] = [5, segment]
            print(self.sendBuff)

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
                print("--------------Expected: ", next)
                # print("--------------out of order segment:\n", data[1])
                self.received += data[1]
                self.seqnum = next
                # print("--------------current seqnum now: ", self.seqnum)
                next += RDTLayer.DATA_LENGTH
                processed += 1
            else:
                continue
        for i in range(processed):
            del self.receiveBuff[0]
        print(self.receiveBuff)


 # ############################################################################################################ #
  # ############################################################################################################ #
        # What segments have been received?
        # How will you get them back in order?
        # This is where a majority of your logic will be implemented

        # How do you respond to what you have received?
        # How can you tell data segments apart from ack segemnts?
        # print('processReceive(): Complete this...')

        # Somewhere in here you will be setting the contents of the ack segments to send.
        # The goal is to employ cumulative ack, just like TCP does...
        # acknum = "0"


        # ############################################################################################################ #
        # Display response segment
        # segmentAck.setAck(acknum)
        # print("Sending ack: ", segmentAck.to_string())

        # Use the unreliable sendChannel to send the ack packet