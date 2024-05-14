# Partially repeats the algorithm of pg_filedump

# Launch example:
```
python3 my_filedump.py path_to_file/16398
```

# Example output:
```
*******************************************************************
* PostgreSQL File/Block Formatted Dump Utility
*
* File: path_to_file/16398
* Options used: -i
*******************************************************************


Block    0 ********************************************************
<Header> -----
Block Offset: 0x00000000         Offsets: Lower      32 (0x0020)
Block: Size 8192  Version    4            Upper    8080 (0x1f90)
LSN:  logid      0 recoff 0x01924808      Special  8192 (0x2000)
Items:    2                      Free Space: 8048
Checksum: 0x0000  Prune XID: 0x00000000  Flags: 0x0000 ()
Length (including item array): 32

<Data> ----- 
Item   1 -- Length:   56  Offset: 8136 (0x1fc8)  Flags: NORMAL
  XMIN: 744 XMAX: 0 CID|XVAC: 0
  Block Id: 0  linp Index: 1   Attributes: 4   Size: 24
  infomask: 0x0902 (HASVARWIDTH|XMIN_COMMITTED|XMAX_INVALID)

Item   2 -- Length:   52  Offset: 8080 (0x1f90)  Flags: NORMAL
  XMIN: 745 XMAX: 0 CID|XVAC: 0
  Block Id: 0  linp Index: 2   Attributes: 4   Size: 24
  infomask: 0x0903 (HASNULL|HASVARWIDTH|XMIN_COMMITTED|XMAX_INVALID)
  t_bits: [0]: 0x05 



*** End of File Encountered. Last Block Read: 0 ***
```