#!/usr/bin/env python
# -*- coding: utf-8
import struct

t_index = [
    -1, -1, -1, -1, 2, 4, 6, 8,
    -1, -1, -1, -1, 2, 4, 6, 8]  # index table

t_step = [
    7, 8, 9, 10, 11, 12, 13, 14,
    16, 17, 19, 21, 23, 25, 28, 31,
    34, 37, 41, 45, 50, 55, 60, 66,
    73, 80, 88, 97, 107, 118, 130, 143,
    157, 173, 190, 209, 230, 253, 279, 307,
    337, 371, 408, 449, 494, 544, 598, 658,
    724, 796, 876, 963, 1060, 1166, 1282, 1411,
    1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024,
    3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
    7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
    15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794,
    32767]  # quantize table

_encoder_predicted = 0
_encoder_index = 0
_encoder_step = 7
_decoder_predicted = 0
_decoder_index = 0
_decoder_step = 7


def _encode_sample(sample):
    # encode one linear pcm sample to ima adpcm neeble
    # using global encoder state
    global _encoder_predicted
    global _encoder_index

    delta = sample - _encoder_predicted

    if delta >= 0:
        value = 0
    else:
        value = 8
        delta = -delta

    step = t_step[_encoder_index]

    diff = step >> 3

    if delta > step:
        value |= 4
        delta -= step
        diff += step
    step >>= 1

    if delta > step:
        value |= 2
        delta -= step
        diff += step
    step >>= 1

    if delta > step:
        value |= 1
        diff += step

    if value & 8:
        _encoder_predicted -= diff
    else:
        _encoder_predicted += diff

    if _encoder_predicted < - 0x8000:
        _encoder_predicted = -0x8000
    elif _encoder_predicted > 0x7fff:
        _encoder_predicted = 0x7fff

    _encoder_index += t_index[value & 7]

    if _encoder_index < 0:
        _encoder_index = 0
    elif _encoder_index > 88:
        _encoder_index = 88

    return value


def _decode_sample(neeble):
    # decode one sample from compressed neeble
    # using global decoder state
    global _decoder_predicted
    global _decoder_index
    global _decoder_step

    difference = 0

    if neeble & 4:
        difference += _decoder_step

    if neeble & 2:
        difference += _decoder_step >> 1

    if neeble & 1:
        difference += _decoder_step >> 2

    difference += _decoder_step >> 3

    if neeble & 8:
        difference = -difference

    _decoder_predicted += difference

    if _decoder_predicted > 32767:
        _decoder_predicted = 32767

    elif _decoder_predicted < -32767:
        _decoder_predicted = - 32767

    _decoder_index += t_index[neeble]
    if _decoder_index < 0:
        _decoder_index = 0
    elif _decoder_index > 88:
        _decoder_index = 88
    _decoder_step = t_step[_decoder_index]

    return _decoder_predicted


def _calc_head(sample):
    # Calculating ima adpcm block head

    # using global _encoder_index
    global _encoder_index
    # calculating global _encoder_index for first sample
    _encode_sample(struct.unpack('h', sample)[0])
    # packing header
    head = sample                            # Uncompressed sample
    head += struct.pack('B', _encoder_index) # Calculated index for sample
    head += struct.pack('B', 0x00)           # Always 0
    return head


def encode_block(block):
    """Encode linear pcm fragment to compressed ima adpcm block.
    Block is a string containing values from wavefile, network, etc.
    Returns a string containing packed compressed ima adpcm block.
    Only 1010 bytes size linear mono 16 bit fragment supported."""
    if len(block) != 1010:
        raise ValueError('Unsupported sample quantity in block. Should be 505.')
        return

    result = _calc_head(block[0:2])

    for i in range(2, len(block)):

        if (i + 1) % 4 == 0:

            sample2 = _encode_sample(struct.unpack('h', block[i - 1:i + 1:])[0])
            sample = _encode_sample(struct.unpack('h', block[i + 1:i + 3:])[0])
            result += struct.pack('B', (sample << 4) | sample2)

    return result


def decode_block(block):
    """Decode compressed ima adpcm block.
    Block is a string containing packed values from wavefile, network, etc.
    Returns a string containing packed uncompressed linear pcm values.
    Only 256 bytes compressed block size supported."""
    if len(block) != 256:
        raise ValueError('Unsupported block size. Should be 256.')
        return

    global _decoder_predicted
    global _decoder_index
    global _decoder_step

    result = ''
    _decoder_predicted = struct.unpack('h', block[0:2])[0]
    _decoder_index = struct.unpack('B', block[2:3])[0]
    _decoder_step = t_step[_decoder_index]
    result += block[0:2]

    for i in range(4, len(block)):
        original_sample = struct.unpack('B', block[i])[0]
        second_sample = original_sample >> 4
        first_sample = (second_sample << 4) ^ original_sample
        result += struct.pack('h', _decode_sample(first_sample))
        result += struct.pack('h', _decode_sample(second_sample))

    return result


__all__ = ["encode_block", "decode_block"]