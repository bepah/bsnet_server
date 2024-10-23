import hashlib
import logging
import math
import socket
import struct
import threading
import traceback
from venv import create


def crypt_data(msg: bytes) -> bytes:
    out = bytearray()
    key = b"\x5A\x70\x85\xAF"

    for i in range(len(msg)):
        out.append(msg[i] ^ key[i % len(key)])

    return bytes(out)


class GameServer:

    LARGE_MESSAGE_SIZE = 0x30 - (2 * 3)

    def __init__(self, conn: socket.socket, addr, logger):
        self.req_id = 0

        self.conn = conn
        self.addr = addr
        self.logger = logger
        self.skip_send = False

        self.dispatch_table = {
            0x0101: self.cmd_login,
            0x0102: self.cmd_register,
            0x0104: self.cmd_front_connect,
            0x0141: self.cmd_heartbeat,

            # 0x4112: self.cmd_login_news,
            # 0x4114: self.cmd_unk1
            0x425b: self.cmd_login_front,
            0x4259: self.cmd_login_thing2
        }

    def make_response(self, command, extra_data: bytes, data_size: int = 0) -> bytes:
        self.req_id += 1
        out = struct.pack("<HBIB", command, data_size, len(extra_data), self.req_id)

        # assert len(extra_data) <= 0x30

        if extra_data is not None:
            out += hashlib.md5(out + extra_data).digest() + extra_data
        else:
            out += hashlib.md5(out).digest()

        return out

    @staticmethod
    def verify_request(data: bytes) -> bool:
        hashed = hashlib.md5(data[:0x8] + data[0x18:]).digest()
        return hashed == data[0x8:0x18]

    @staticmethod
    def pad_bytes(data: bytes, size: int) -> bytes:
        return data.ljust(size, b"\x00")

    def send_large_message(self, cmd: int, message: bytes):
        self.skip_send = True

        total_message_size = math.ceil(len(message) / self.LARGE_MESSAGE_SIZE)
        for part in range(total_message_size):
            chunk = message[part * self.LARGE_MESSAGE_SIZE:(part + 1) * self.LARGE_MESSAGE_SIZE]

            self.logger.info(f"< [large] {part + 1}/{total_message_size} cmd=0x{cmd:04x}, "
                              f"chunk[0x{len(chunk):02x}]={chunk}")

            self.conn.sendall(crypt_data(
                self.make_response(
                    cmd,
                    struct.pack(">HHH", total_message_size, part + 1, len(chunk)) + chunk
                )
            ))

    def parse_command(self) -> bool:
        data = self.conn.recv(1024)
        data = crypt_data(data)

        if not self.verify_request(data):
            self.logger.error(f"Invalid md5 hash for {data}")
            self.conn.close()
            return False

        req_cmd, req_size = struct.unpack_from(">HB", data)

        self.logger.info(f"> cmd=0x{req_cmd:04x}, data={data}")

        if req_cmd == 0x0142:# or req_cmd == 0x425b:
            self.conn.close()
            self.logger.info(f"Disconnected from {self.addr}")
            return False

        response_fnc = self.dispatch_table.get(req_cmd)

        if not response_fnc:
            self.logger.warning(f"Unknown command 0x{req_cmd:04x}, disconnecting...")
            # Make dummy response to capture at breakpoint
            self.conn.send(crypt_data(self.make_response(0xbeef, b"\0" * 0x30)))
            self.conn.close()
            return False

        self.skip_send = False
        data = response_fnc(data)

        if self.skip_send is False:
            self.logger.info(f"< {data}")
            self.conn.sendall(crypt_data(data))

        return True

    def cmd_login(self, data: bytes) -> bytes:
        """
        Called on checking if the user is valid to login
        and a valid account exists, otherwise tell the game
        to register for one.
        """
        # to_send = make_response(0x0001, struct.pack(">h", -301))  # New user
        ip_addr = struct.unpack("@I", socket.inet_aton(self.addr[0]))[0]
        return self.make_response(
            0x0301,
            # IP, port, remaining params have something to do with news or something
            struct.pack(">IHIH", ip_addr, 5730, 0, 0)
        )

    def cmd_register(self, data: bytes) -> bytes:
        """
        Called when registering a user, provided birthday and
        name. Returns back the same response as a login.
        """
        # TODO not implemented
        return self.cmd_login(data)

    def cmd_front_connect(self, data: bytes) -> bytes:
        """
        Called on connected to the front server from the gate server,
        unknown parameters.
        """
        return self.make_response(0x0501, struct.pack(">HHI", 0, 0, 0))

    def cmd_heartbeat(self, data: bytes) -> bytes:
        """
        Called once in a while to maintain connection to the server.
        """
        return self.make_response(3, struct.pack(">HHH", 0, 0, 0) + b"\0" * 0x10)

    def cmd_login_news(self, data: bytes):
        """
        Retrieves news for a user when logged in
        """
        content = b"Hello world\n\nmessage 123"
        msg = struct.pack("<HHII", 1, 1, 0, len(content))  # current, total, unknown, length
        msg += self.pad_bytes(b"Name", 0x14)
        msg += self.pad_bytes(b"Time", 0x80)
        msg += content
        self.send_large_message(0x1401, msg)

    def cmd_login_front(self, data: bytes):
        msg = self.pad_bytes(b"hello", 0x40)
        msg += struct.pack("<BBBI", 0, 0, 0, 0)
        msg += self.pad_bytes(b"world", 0x20)
        msg += struct.pack("<HHHHHHH", 0, 0, 0, 0, 0, 0, 0)
        msg += struct.pack("<BBIHHHHI", 0, 0, 0, 0, 0, 0, 0, 0)
        return self.make_response(0x1601, msg, 0)

    def cmd_login_thing2(self, data: bytes):
        # msg = struct.pack("<HHBBHHBHH", 0, 0, 0, 0, 0, 0, 0, 0, 0)
        msg = b"\0" * 512
        return self.make_response(0x5A02, msg)

def handle_connection(conn: socket.socket, addr, logger):
    logger.info(f"Connected from {addr}")

    state = GameServer(conn, addr, logger)

    try:
        while state.parse_command():
            pass
    except:
        conn.close()

        traceback.print_exc()


def create_logger():
    logger = logging.getLogger("game_server")

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def main():
    logger = create_logger()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 5730))
        s.listen()

        logger.info("Listening...")

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
                args=(conn, addr, logger)
            ).start()


if __name__ == "__main__":
    main()
