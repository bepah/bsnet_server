import argparse
import os
import struct


def extract_bin(in_file: str, out_folder: str):
    with open(in_file, "rb") as f:
        assert f.read(4) == b"PKDT"
        assert struct.unpack("<I", f.read(4))[0] == 1

        file_size, num_a, item_count, current_pos, maybe_crc = struct.unpack("<IIIII", f.read(4 * 5))
        assert (file_size - 0x20) > 0

        for i in range(item_count):
            f.seek(current_pos, os.SEEK_SET)

            item_length, pos, size, crc = struct.unpack("<IIII", f.read(16))
            assert (item_length - 0x10) > 0

            name_chunk = f.read(item_length - 0x10)
            try:
                name = name_chunk.rstrip(b"\0").decode("shift-jis")
            except UnicodeDecodeError:
                raise ValueError(f"Invalid name {name_chunk} in {in_file}")

            extract_path = os.path.join(out_folder, name)

            if os.path.isfile(extract_path):
                continue

            print(f"Extracting {name}")
            os.makedirs(os.path.dirname(extract_path), exist_ok=True)

            current_pos = f.tell()
            f.seek(pos)

            zero, header_size, size2, crc2 = struct.unpack("<IIII", f.read(16))

            assert zero == 0
            assert header_size == 0x10
            assert size == size2
            assert crc == crc2

            with open(extract_path, "wb") as w:
                w.write(f.read(size))


def extract_all(in_folder: str, out_folder: str):
    for file in os.listdir(in_folder):
        if not file.endswith(".bin"):
            print(f"Skipping {file}")
            continue

        extract_bin(
            os.path.join(in_folder, file),
            os.path.join(out_folder, file.replace(".bin", ""))
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("in_folder")
    parser.add_argument("out_folder")
    args = parser.parse_args()
    extract_all(args.in_folder, args.out_folder)


if __name__ == "__main__":
    main()
