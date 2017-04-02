#!/usr/bin/env python3
"""
Patch for dmcr.exe (Cossacks, American Conquest)
https://habrahabr.ru/post/277067/
"""

import sys
import os

from collections import namedtuple

Link = namedtuple('Link', ('prefix', 'suffix_size'))

CHAIN = (
    Link(b'\x7D\x3C', 0),  # 0  jnl  dmcr.CDGINIT_EnCD+17F1
    Link(b'\xE8', 4),      # 1  call dmcr.ProcessMessages
    Link(b'\x33\xC0', 0),  # 2  xor  eax, eax
    Link(b'\xA0', 4),      # 3  mov  al, dmcr.fon30y5+24
    Link(b'\x85\xC0', 0),  # 4  test eax, eax
    Link(b'\x74\x05', 0),  # 5  je   dmcr.CDGINIT_EnCD+17CA
    Link(b'\xE8', 4),      # 6  call dmcr.UnPress+846
    Link(b'\xE8', 4),      # 7  call cmcr.PlayRecFile+6AB3
    Link(b'\x2B\x05', 4),  # 8  sub  eax, dmcr.fon30y5+64
    Link(b'\x8B\x0D', 4),  # 9  mov  ecx, dmcr.FPSTime
    Link(b'\x03\x0D', 4),  # 10 add  ecx, dmcr.FPSTime
    Link(b'\x3B\xC1', 0),  # 11 cmp  eax, ecx
    Link(b'\x7C\xD0', 0),  # 12 jl   dmcr.CDGINIT_EnCD+17B5
    Link(b'\x33\xD2', 0),  # 13 xor  edx, edx
    Link(b'\x8A\x15', 4),  # 14 mov  dl, dmcr.fon30y5+24
    Link(b'\x85\xD2', 0),  # 15 test edx, edx
    Link(b'\x75\xC4', 0),  # 16 jne  dmcr.CDGINIT_EnCD+17B5
)
LINKS_PREFIXES_REPLACE_TABLE = {
    0: '\xEB\x15',
    12: '\x7C\xE5',
    16: '\x90\x90',
}


def main():
    data = read_data(sys.argv[1])
    links_positions = find_chain(data, CHAIN)
    verify_links_positions(data, CHAIN, links_positions)
    data = replace_links_prefixes(data, links_positions, LINKS_PREFIXES_REPLACE_TABLE)
    sys.stdout.buffer.write(data)


def read_data(file_name):
    size = os.stat(file_name).st_size
    with open(file_name, 'rb') as f:
        return f.read(size)


def find_chain(data, chain):
    position = 0
    link_index = 0
    links_positions = [None] * len(chain)
    while True:
        if link_index >= len(chain):
            break
        current_link = chain[link_index]
        position = data.find(current_link.prefix, position)
        if position == -1:
            break
        if link_index == 0 or position - links_positions[link_index - 1] == len(chain[link_index - 1].prefix) + chain[link_index - 1].suffix_size:
            links_positions[link_index] = position
            link_index += 1
            position += len(current_link.prefix) + current_link.suffix_size
        else:
            position = links_positions[0] + 1
            links_positions = [None] * len(chain)
            link_index = 0
    return links_positions


def verify_links_positions(data, chain, links_positions):
    for link, position in zip(chain, links_positions):
        assert link.prefix == data[position:position + len(link.prefix)]


def replace_links_prefixes(data, links_positions, replace_table):
    new_data = bytearray(data)
    for link_index, new_prefix in replace_table.items():
        position = links_positions[link_index]
        for i in range(len(new_prefix)):
            new_data[position + i] = ord(new_prefix[i])
    return bytes(new_data)


if __name__ == '__main__':
    main()
