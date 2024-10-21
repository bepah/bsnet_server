import hashlib
import socket
import struct
import threading
import traceback


def crypt_data(msg: bytes) -> bytes:
    out = bytearray()
    key = b"\x5A\x70\x85\xAF"

    for i in range(len(msg)):
        out.append(msg[i] ^ key[i % len(key)])

    return bytes(out)


def make_response(command, req_id, extra_data: bytes) -> bytes:
    out = struct.pack("<HBIB", command, 0, len(extra_data), req_id)

    assert len(extra_data) <= 0x30

    if extra_data is not None:
        out += hashlib.md5(out + extra_data).digest() + extra_data
    else:
        out += hashlib.md5(out).digest()

    return out


def handle_connection(conn, addr):
    print("Connected from", addr)

    while True:
        data = conn.recv(1024)
        data = crypt_data(data)

        hashed = hashlib.md5(data[:0x8] + data[0x18:]).digest()

        if hashed != data[0x8:0x18]:
            print(f"Invalid md5 hash for {data}")
            conn.close()
            return

        command, req_id = struct.unpack_from("<H5xB", data)

        print(f"> [{req_id}] 0x{command:02x} | {data}")

        if command == 0x4201 or command == 0x5b42:
            conn.close()
            print("Disconnected from", addr)
            return
        elif command == 0x0101:
            # to_send = make_response(0x0001, struct.pack(">h", -301))  # New user
            ip_addr = struct.unpack("@I", socket.inet_aton(addr[0]))[0]
            to_send = make_response(0x0301, req_id, struct.pack(">IHIH", ip_addr, 5730, 0xdead, 0xbeef))
        # elif command == 0x0201:
            # Register user
            # to_send = make_response(0x0301, struct.pack(">IHIH", 1, 1, 1, 1))
        elif command == 0x401:
            # -300, if we have more data to send
            # to_send = make_response(0x0001, req_id, struct.pack(">h", -300))
            to_send = make_response(0x0501, req_id, struct.pack(">HHI", 0, 0, 0))
        elif command == 0x1241:
            # News at login, gifts?
            # to_send = make_response(0x0001, req_id, struct.pack(">h", -301))
            to_send = make_response(0x1301, req_id, struct.pack(">HHH", 1, 1, 3) + b"\0" * 0x20)
        elif command == 0x1441:
            to_send = make_response(0x1301, req_id, struct.pack(">HHH", 3, 3, 3) + b"\0" * 0x20)
        elif command == 0x4101:
            # Heartbeat?
            to_send = make_response(3, req_id, struct.pack(">HHH", 0, 0, 0) + b"\0" * 0x10)
        else:
            print("Unknown command, disconnecting...", hex(command))
            conn.close()
            return

        print(f"< [{req_id}]", to_send)
        conn.send(crypt_data(to_send))


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 5730))
        s.listen()

        print("Listening...")

        while True:
            try:
                conn, addr = s.accept()
            except KeyboardInterrupt:
                break
            except:
                traceback.print_exc()
                continue

            threading.Thread(
                target=handle_connection,
                args=(conn, addr)
            ).start()


if __name__ == "__main__":
    main()
