# pyima
This python module implements an audio codec IMA ADPCM suitable for use in
games or other audio applications. It support 256 bytes compressed blocks
with 505 4-bit samples at sample rate 8 KHz mono and 1010 bytes uncompressed
blocks with 505 16-bit samples at sample rate 8 KHz mono.
16-bit data samples encoded as 4-bit differences result in 4:1 compression format.
