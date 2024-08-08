import struct
import sys

PTE_STRUCT = "<1s3s1s3sII"
EBR_STRUCT = "<446s16s16s16s16s2s"
SECTOR_SIZE = 512
PTO = 446

PT_TYPES = {
    "NTFS": b'\x07',
    "EXT": b'\x05',
    "FAT32": [b'\x0B', b'\x0C']
}

def parse_entry(entry):
    pte = struct.unpack(PTE_STRUCT, entry)
    ptype = pte[2]
    start = pte[4]
    size = pte[5]
    return ptype, start, size

def fs_type(ptype):
    if ptype in PT_TYPES["FAT32"]:
        return "FAT32"
    elif ptype == PT_TYPES["NTFS"]:
        return "NTFS"
    return None

def read_mbr(file):
    with open(file, 'rb') as f:
        mbr = f.read(SECTOR_SIZE)
        partitions = []
        for i in range(4):
            entry = mbr[PTO + i * 16: PTO + (i + 1) * 16]
            ptype, start, size = parse_entry(entry)
            fs = fs_type(ptype)
            if fs:
                partitions.append((fs, start, size))
            elif ptype == PT_TYPES["EXT"]:
                partitions.extend(read_ebr(file, start))
        return partitions

def read_ebr(file, start):
    parts = []
    base = start
    with open(file, 'rb') as f:
        f.seek(start * SECTOR_SIZE)
        while True:
            ebr = f.read(SECTOR_SIZE)
            if not ebr or len(ebr) < SECTOR_SIZE:
                break
            ebr_data = struct.unpack(EBR_STRUCT, ebr)
            p1 = ebr_data[1]
            p2 = ebr_data[2]
            ptype, rel_start, size = parse_entry(p1)
            fs = fs_type(ptype)
            if fs:
                fs_start = start + rel_start
                parts.append((fs, fs_start, size))
            next_rel_start = parse_entry(p2)[1]
            if next_rel_start == 0:
                break
            start = base + next_rel_start
            f.seek(start * SECTOR_SIZE)
    return parts

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 mbr_parser.py <image>")
        sys.exit(1)
    img = sys.argv[1]
    parts = read_mbr(img)
    for fs, start, size in parts:
        print(f"{fs} {start} {size}")

if __name__ == "__main__":
    main()
