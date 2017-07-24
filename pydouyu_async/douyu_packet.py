from struct import pack, unpack

MESSAGE_TYPE_FROM_CLIENT = 689
MESSAGE_TYPE_FROM_SERVER = 690

def to_raw(body,encrypt=0,reserved=0):
    if isinstance(body,str):
        body = body.encode('utf-8')
    raw_length = len(body) + 9
    msg_type = MESSAGE_TYPE_FROM_CLIENT
    return pack('<llhbb%ds' % (len(body) + 1), raw_length, raw_length, msg_type, encrypt, reserved, body + b'\0')

def from_raw(buff,remains= None):
    # Packet Part 1: Bytes[0-3] Packet length in little endian
    # Packet Part 2: Bytes[4-7] Same packet length in little endian
    # Packet Part 3: Bytes[8-9] Message type, 689(FromClient), 690(FromServer)
    # Packet Part 4: Bytes[10] Encryption Field - Reserved
    # Packet Part 5: Bytes[11] Reserved
    # Packet Part 6: Bytes[12-] Messege body in UTF8

    if remains is not None:
        buff = remains + buff
    parsed_buff = []
    while True:
        buff_len = len(buff)
        if buff_len < 12:
            return parsed_buff, buff
        packet_length_1, packet_length_2, msg_type, encryption, reserved, body = unpack('<llhbb%ds' % (buff_len - 12), buff)
        if packet_length_1 != packet_length_2:
            return parsed_buff,None
        needed_body_length = packet_length_1 - 8
        current_body_length = len(body)
        if current_body_length < needed_body_length:
            return parsed_buff,buff
        elif current_body_length > needed_body_length:
            parsed_buff.append(body[0:needed_body_length])
            buff = buff[12 + needed_body_length:]
        else:
            parsed_buff.append(body[0:needed_body_length])
            return parsed_buff,None
