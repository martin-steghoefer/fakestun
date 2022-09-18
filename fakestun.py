#!/usr/bin/env python3


#######################################################
# Configuration                                       #
#######################################################


# IP address and UDP port to use for incoming requests
LISTEN_IP=""                # Required
LISTEN_PORT=3478            # Required; normally 3478


# STUN response:

# MAPPED-ADDRESS attribute of response
RESPONSE_MAPPED_IP=""       # Fixed IP to return; if empty, returns the IP the request came from
RESPONSE_MAPPED_PORT=-1     # Fixed Port to return; if negative, returns the port the request came from

# SOURCE-ADDRESS attribute of response
RESPONSE_SOURCE_IP=""       # If empty, LISTEN_IP is used
RESPONSE_SOURCE_PORT=-1     # If negative, LISTEN_PORT is used

# CHANGED-ADDRESS attribute of response
RESPONSE_CHANGED_IP=""      # If empty, no attribute CHANGED-ADDRESS will be returned
RESPONSE_CHANGED_PORT=-1    # If negative, no attribute CHANGED-ADDRESS will be returned


#######################################################


import ipaddress
import socket


""" Convert number to its unsigned 8 Bit integer representation as constant byte array """
def UInt8ToBytes(number):
    return number.to_bytes(1, byteorder = 'big', signed = False)

""" Convert number to its unsigned 16 Bit integer representation as constant byte array """
def UInt16ToBytes(number):
    return number.to_bytes(2, byteorder = 'big', signed = False)

""" Convert number to its unsigned 32 Bit integer representation as constant byte array """
def UInt32ToBytes(number):
    return number.to_bytes(4, byteorder = 'big', signed = False)


""" STUN response attribute """
class Attribute:
    def __init__(self, attributeType):
        self.__attributeType = attributeType

    def getBinary(self):
        attributeValue = self.getAttributeValue()
        return UInt16ToBytes(self.__attributeType) + UInt16ToBytes(len(attributeValue)) + attributeValue


""" STUN response attribute consisting of IPv4 address and Port (e.g. for MAPPED-ADDRESS) """
class IPv4AddressAndPortAttribute(Attribute):
    TYPE_MAPPED_ADDRESS=1
    TYPE_SOURCE_ADDRESS=4
    TYPE_CHANGED_ADDRESS=5

    def __init__(self, attributeType, ip, port):
        super().__init__(attributeType)
        self.__ip = ip
        self.__port = port

    def getAttributeValue(self):
        protocolIPv4 = UInt16ToBytes(1)
        port = UInt16ToBytes(self.__port)
        ip = self.__ip
        return protocolIPv4 + port + ip


""" STUN response attribute consisting of only a string (e.g. for SERVER) """
class TextAttribute(Attribute):
    TYPE_SERVER=32802

    def __init__(self, attributeType, text):
        super().__init__(attributeType)
        self.__text = text

    def getAttributeValue(self):
        return self.__text.encode("utf-8") + b"\x00"


""" Complete information for a STUN response message """
class ResponseMessage:
    """ Message type corresponding to the response to a Binding Request """
    BINDING_RESPONSE=257

    def __init__(self, messageType, messageTransactionID):
        self.__messageType = messageType
        self.__messageTransactionID = messageTransactionID
        self.__attributes = []

    def addAttribute(self, attribute):
        self.__attributes.append(attribute)

    def getBinary(self):
        attributesBinary = b''.join(map(lambda attribute : attribute.getBinary(), self.__attributes))
        return UInt16ToBytes(self.__messageType) \
             + UInt16ToBytes(len(attributesBinary)) \
             + self.__messageTransactionID \
             + attributesBinary


def getConfigurationIpAndPort(ip, port, defaultIP, defaultPort):
    bothConfigured = True
    if ip:
        ip = ipaddress.IPv4Address(ip).packed
    else:
        ip = defaultIP
        bothConfigured = False
    if port < 0:
        port = defaultPort
        bothConfigured = False
    return (ip, port, bothConfigured)


""" Main loop to start the server, wait for requests and respond. """
def startServer():
    listenIpPacked = ipaddress.IPv4Address(LISTEN_IP).packed

    # Listen
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, LISTEN_PORT))
    print("Server started. Waiting for incoming requests.")

    while True:
        data, addr = sock.recvfrom(1024)
        if data[0:2] == UInt16ToBytes(1):
            print("Received request. Sending response.")

            response = ResponseMessage(ResponseMessage.BINDING_RESPONSE, data[4:20])

            # MAPPED-ADDRESS attribute
            mappedIp, mappedPort, _ = getConfigurationIpAndPort(
                    RESPONSE_MAPPED_IP, RESPONSE_MAPPED_PORT, ipaddress.IPv4Address(addr[0]).packed, addr[1])
            response.addAttribute(IPv4AddressAndPortAttribute(
                    IPv4AddressAndPortAttribute.TYPE_MAPPED_ADDRESS,
                    mappedIp,
                    mappedPort))

            # SOURCE-ADDRESS attribute
            sourceIp, sourcePort, _ = getConfigurationIpAndPort(
                    RESPONSE_SOURCE_IP, RESPONSE_SOURCE_PORT, listenIpPacked, LISTEN_PORT)
            response.addAttribute(IPv4AddressAndPortAttribute(
                    IPv4AddressAndPortAttribute.TYPE_SOURCE_ADDRESS,
                    sourceIp,
                    sourcePort))

            # CHANGED-ADDRESS attribute
            changedIp, changedPort, changedConfigured = getConfigurationIpAndPort(
                    RESPONSE_CHANGED_IP, RESPONSE_CHANGED_PORT, None, None)
            if changedConfigured:
                response.addAttribute(IPv4AddressAndPortAttribute(
                        IPv4AddressAndPortAttribute.TYPE_CHANGED_ADDRESS,
                        changedIp,
                        changedPort))

            # SERVER attribute
            response.addAttribute(TextAttribute(TextAttribute.TYPE_SERVER, "Fake response with static hard-coded IP address"))

            # Assemble and send
            sock.sendto(response.getBinary(), addr)
        else:
            print("Received a message that this primitive dummy library does not understand.")


if __name__ == '__main__':
    startServer()
