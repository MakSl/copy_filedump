#!/usr/bin/env python3

import sys
import os
import argparse
import struct

format_str = "IIHHHHHHI"
PD_HAS_FREE_LINES = 0x0001
PD_PAGE_FULL = 0x0002
PD_ALL_VISIBLE = 0x0004

class LPFlags():
	LP_UNUSED = 0		# unused (should always have lp_len=0)
	LP_NORMAL = 1		# used (should always have lp_len>0)
	LP_REDIRECT = 2		# HOT redirect (should have lp_len=0)
	LP_DEAD = 3			# dead, may or may not have storage

HEAP_HASNULL = 0x0001			# has null attribute(s)
HEAP_HASVARWIDTH = 0x0002		# has variable-width attribute(s)
HEAP_HASEXTERNAL = 0x0004		# has external stored attribute(s)
HEAP_HASOID_OLD = 0x0008		# has an object-id field
HEAP_XMAX_KEYSHR_LOCK = 0x0010	# xmax is a key-shared locker
HEAP_COMBOCID = 0x0020			# t_cid is a combo CID
HEAP_XMAX_EXCL_LOCK = 0x0040	# xmax is exclusive locker
HEAP_XMAX_LOCK_ONLY = 0x0080	# xmax, if valid, is only a locker

HEAP_XMIN_COMMITTED = 0x0100	# t_xmin committed
HEAP_XMIN_INVALID = 0x0200		# t_xmin invalid/aborted
HEAP_XMIN_FROZEN = HEAP_XMIN_COMMITTED | HEAP_XMIN_INVALID
HEAP_XMAX_COMMITTED = 0x0400	# t_xmax committed
HEAP_XMAX_INVALID = 0x0800		# t_xmax invalid/aborted
HEAP_XMAX_IS_MULTI = 0x1000		# t_xmax is a MultiXactId
HEAP_UPDATED = 0x2000			# this is UPDATEd version of row
HEAP_MOVED_OFF = 0x4000			# moved to another place by pre-9.0
								# VACUUM FULL; kept for binary
								# upgrade support
HEAP_MOVED_IN = 0x8000			# moved from another place by pre-9.0
								# VACUUM FULL; kept for binary
								# upgrade support

HEAP_NATTS_MASK	= 0x07FF		# 11 bits for number of attributes

HEAP_KEYS_UPDATED = 0x2000		# tuple was updated and key cols
								# modified, or tuple deleted
HEAP_HOT_UPDATED = 0x4000		# tuple was HOT-updated
HEAP_ONLY_TUPLE = 0x8000		# this is heap-only tuple

def format_header(buffer, current_block, block_size):
	print("<Header> -----")
	values = struct.unpack(format_str, buffer[:24])
	max_offset = 0 if values[4] <= 24 else (values[4] - 24) // 4

	if max_offset > 0:
		items_length = max_offset * 4
		header_bytes = 24 + items_length
	flag_string = ""
	if values[3] & PD_HAS_FREE_LINES:
		flag_string += "HAS_FREE_LINES|"
	if values[3] & PD_PAGE_FULL:
		flag_string += "PAGE_FULL|"
	if values[3] & PD_ALL_VISIBLE:
		flag_string += "ALL_VISIBLE|"

	flag_string = flag_string[:-1]
	page_offset = block_size * current_block

	print("Block Offset: 0x%08x         Offsets: Lower    %4u (0x%04hx)" % (page_offset, values[4], values[4]))
	print("Block: Size {:4d}  Version {:4}            Upper    {:4} (0x{:04x})".format(values[7] & (0xFF00),
																					values[7] & (0x00FF), values[5], values[5]))
	print("LSN:  logid %6d recoff 0x%08x      Special  %4u (0x%04hx)" % (values[0], values[1], values[6], values[6]))
	print(f"Items: {max_offset:4d}                      Free Space: {values[5] - values[4]:4}")
	print("Checksum: 0x{:04x}  Prune XID: 0x{:08x}  Flags: 0x{:04x} ({})".format(values[2], values[8], values[3], flag_string))
	print("Length (including item array): {}\n".format(header_bytes))

def Format_item_block(buffer):
	print("<Data> ----- ")
	values = struct.unpack(format_str, buffer[:24])
	max_offset = 0 if values[4] <= 24 else (values[4] - 24) // 4
	values = struct.unpack("I" * max_offset, buffer[24:24 + max_offset * 4])

	if max_offset == 0:
		print("Empty block - no items listed \n\n")
	else:
		text_flags = ""
		for x in range(1, max_offset + 1):
			item_id = values[x - 1]
			item_flags = item_id >> 15 & 0b11
			item_size = item_id >> 17
			item_offset = item_id & 0x7FFF

			match item_flags:
				case LPFlags.LP_UNUSED:
					text_flags = "UNUSED"
				case LPFlags.LP_NORMAL:
					text_flags = "NORMAL"
				case LPFlags.LP_REDIRECT:
					text_flags = "REDIRECT"
				case LPFlags.LP_DEAD:
					text_flags = "DEAD"
				case default:
					text_flags = f"0x{item_flags:02x}"

			print("Item {0:3d} -- Length: {1:4d}  Offset: {2:4d} (0x{2:04x})  Flags: {3}".format(x, item_size, item_offset, text_flags))

			values2 = struct.unpack('IIIHHHHHB', buffer[item_offset:item_offset + 23])
			local_natts = values2[6] & 0x07FF

			print(f"  XMIN: {2 if (values2[7] & 0x0300) == 0x0300 else values2[0]} "
					f"XMAX: {values2[1]} "
					f"CID|XVAC: {values2[2]}")

			print(f"  Block Id: {(values2[3] << 16) | values2[4]}  "
		 			f"linp Index: {values2[5]}   "
					f"Attributes: {local_natts}   Size: {values2[8]}")

			flag_string = ""
			info_mask = values2[7]
			info_mask2 = values2[6]
			if info_mask & HEAP_HASNULL:
				flag_string += "HASNULL|"
			if info_mask & HEAP_HASVARWIDTH:
				flag_string += "HASVARWIDTH|"
			if info_mask & HEAP_HASEXTERNAL:
				flag_string += "HASEXTERNAL|"

			if info_mask & HEAP_XMAX_KEYSHR_LOCK:
				flag_string += "XMAX_KEYSHR_LOCK|"
			if info_mask & HEAP_COMBOCID:
				flag_string += "COMBOCID|"
			if info_mask & HEAP_XMAX_EXCL_LOCK:
				flag_string += "XMAX_EXCL_LOCK|"
			if info_mask & HEAP_XMAX_LOCK_ONLY:
				flag_string += "XMAX_LOCK_ONLY|"
			if info_mask & HEAP_XMIN_COMMITTED:
				flag_string += "XMIN_COMMITTED|"
			if info_mask & HEAP_XMIN_INVALID:
				flag_string += "XMIN_INVALID|"
			if info_mask & HEAP_XMAX_COMMITTED:
				flag_string += "XMAX_COMMITTED|"
			if info_mask & HEAP_XMAX_INVALID:
				flag_string += "XMAX_INVALID|"
			if info_mask & HEAP_XMAX_IS_MULTI:
				flag_string += "XMAX_IS_MULTI|"
			if info_mask & HEAP_UPDATED:
				flag_string += "UPDATED|"
			if info_mask & HEAP_MOVED_OFF:
				flag_string += "MOVED_OFF|"
			if info_mask & HEAP_MOVED_IN:
				flag_string += "MOVED_IN|"

			if info_mask2 & HEAP_KEYS_UPDATED:
				flag_string += "KEYS_UPDATED|"
			if info_mask2 & HEAP_HOT_UPDATED:
				flag_string += "HOT_UPDATED|"
			if info_mask2 & HEAP_ONLY_TUPLE:
				flag_string += "HEAP_ONLY|"

			flag_string = flag_string[:-1]
			print(f"  infomask: 0x{info_mask:04x} ({flag_string})")

			if info_mask & HEAP_HASNULL:
				bitmap_length = (local_natts + 7) // 8
			else:
				bitmap_length = 0

			values2 = struct.unpack('B' * bitmap_length, buffer[item_offset + 23:item_offset + 23 + bitmap_length * 1])

			if (info_mask & HEAP_HASNULL) and bitmap_length:
				print("  t_bits: ", end="")
				for y in range(bitmap_length):
					print(f"[{y}]: 0x{values2[y]:02x} ", end="")
					if (y & 0x03) == 0x03 and y < bitmap_length - 1:
						print("\n          ", end="")
				print("")
			print("")
			if x == max_offset:
				print("")

def format_block(buffer, current_block, block_size):
	print(f"\nBlock {current_block:4} ********************************************************")
	format_header(buffer, current_block, block_size)

def get_block_size(path_to_file):
	with open(path_to_file, "rb") as fd:
		data = fd.read(struct.calcsize(format_str))
		values = struct.unpack(format_str, data)
		block_size = values[7] & (0xFF00)
	return block_size

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Implementation of the pg_filedump functionality')
	parser.add_argument('path_to_file', type=str, help='The path to the file')
	args = parser.parse_args()

	print("\n*******************************************************************\n"
		f"* PostgreSQL File/Block Formatted Dump Utility\n"
		"*\n"
		f"* File: {args.path_to_file}\n"
		"* Options used: -i\n"
		"*******************************************************************\n")
	block_size = get_block_size(args.path_to_file)
	with open(args.path_to_file, "rb") as fd:
		contents_to_dump = 1
		current_block = 0
		buffer = None

		while contents_to_dump:
			buffer = fd.read(block_size)
			if not buffer:
				print(f"\n*** End of File Encountered. Last Block Read: {current_block - 1} ***")
				contents_to_dump = 0
			else:
				format_block(buffer, current_block, block_size)
				Format_item_block(buffer)
				current_block += 1
