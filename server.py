"""Simple server program that works"""
import os
import socket
import enum
import random
import threading
import logging
import json
from logging.handlers import RotatingFileHandler
from icecream import ic

from game_objects import Board
from client import get_other, parse_loc


class ConnectionState(enum.Enum):
    """Enum representing the connections game state"""
    waiting_for_oponent = 1
    initializing_game = 2
    playing = 3
    finished = 4


class Game:
    """Hosts the game elements"""
    def __init__(self, server, player1, player2):
        self.server = server
        server.remove_waiting()
        self.board = Board()
        self.play_state = pick_starter()
        self.players = [player1, player2]
        self.game_thread = threading.Thread(target=self.start)
        self.game_thread.start()
        self.recv_dict = {}

    def start_wait_to_recieve(self, player, i):
        """Start a thread that waits for the player's client to respond"""
        recv_thread = threading.Thread(target=lambda: self.recieve(player, i))
        recv_thread.start()

    def recieve(self, player, out_index):
        """request to reiceve from the players connection"""
        self.recv_dict[out_index] = player.recieve()

    def wait_for_responses(self):
        """Waits for responses from both clients """
        for i, player in enumerate(self.players):
            ic(f"attempt to recieve from {player.address}")
            # adds responses to recv_dict
            self.start_wait_to_recieve(player, i)

        while len(self.recv_dict) < 2:
            if self.server.stop or not self.check_connections():
                return None
        ic(self.recv_dict)
        ret = self.recv_dict[int(self.play_state[0])-1]
        self.recv_dict = {}
        return ret

    def start(self):
        """Start the game running"""
        # Send player's number and starting player
        for i, player in enumerate(self.players):
            data = f"{i+1},{self.play_state[0]}"
            ic(player.address, data)
            player.send(data)

        check_connection = self.check_connections()
        print(f"check_connections {check_connection}")
        if not check_connection:
            self.abort_game()
            return

        # Now do the game loop
        while not self.server.stop and self.check_connections():
            self.play_round()

    def play_round(self):
        """Play a round between the two connected clients"""
        picked_piece = self.wait_for_responses()
        if picked_piece is None:
            return

        check_connection = self.check_connections()
        for player in self.players:
            print("player connected?" + str(player.connected))
        print(f"check_connections {check_connection}")
        if not check_connection:
            self.abort_game()
            return

        print("End of func", picked_piece)
        # initially player only picks a piece
        # Send both players confirmation of the piece chosen
        self.send_to_players(picked_piece)
        # Change state to be that the other chooses
        self.play_state = f"{get_other(self.play_state[0])}p"

        picked_location = self.wait_for_responses()

        check_connection = self.check_connections()
        print(f"check_connections {check_connection}")
        if not check_connection:
            self.abort_game()
            return

        ic(picked_location)
        self.send_to_players(picked_location)
        i, j = parse_loc(picked_location)
        self.board.play_move(i, j, picked_piece)

        self.play_state = f"{self.play_state[0]}c"
        if self.board.check_win():
            self.end_game()

    def end_game(self):
        """End the connections between the server and players"""
        for player in self.players:
            player.close()

    def send_to_players(self, data):
        """Send the data to both players in the game"""
        for player in self.players:
            ic(f"sent to {player.address}")
            player.send(data)

    def check_connections(self):
        """tests if all players are connectd"""
        return all(player.connected for player in self.players)

    def abort_game(self):
        """aborts all connected players"""
        for player in self.players:
            print(player.connected)
            if player.connected:
                player.abort()


def pick_starter():
    """Pick which player starts randomly"""
    return random.choice(["1c", "2c"])


class Connection:
    """Represents a connection to the server"""
    def __init__(self, server, conn, address, state):
        """Connection to the server"""
        self.server = server
        self.logger = server.logger
        self.conn = conn
        self.address = address
        self.state = ConnectionState(state)
        self.connected = True

    def getConn(self):
        """Gret the connections conn"""
        return self.conn

    def getAddress(self):
        """Get the connections address"""
        return self.address

    def initialize(self):
        """If a connection was waiting then this is called to tell it that an opponent was found"""
        self.state = ConnectionState(2)

    def send(self, data):
        """Send the given data to the client"""
        try:
            self.conn.send(data.encode())
        except (ConnectionAbortedError, ConnectionResetError):
            self.connected = False
        else:
            self.connected = True

    def recieve(self):
        """Recieve data from the connection"""
        if not self.connected:
            return None
        try:
            data = self.conn.recv(1024).decode()
        except (ConnectionResetError, ConnectionAbortedError):
            self.connected = False
            return None
        ic(data)
        if data == "":
            self.connected = False
            return None
        self.connected = True
        return data

    def abort(self):
        """Abort the connected client connection"""
        self.logger.warning("A player disconnected, finding the other player a new game")
        if self.connected:
            self.server.connection_game_sort(self)

    def close(self):
        """close connection"""
        self.connected = False
        self.logger.info("Closing connection from %s", self.address)
        self.conn.close()


class ServerProgram:
    """Server program"""
    def __init__(self):
        """Initialize server and start listening for connections"""
        self.logger = setup_logging()

        # get the hostname
        # host = socket.gethostname()
        # host = "localhost"
        # port = 5000  # initiate port no above 1024
        with open("config.json", "r") as f:
            config = json.load(f)
            host = config["host"]
            port = int(config["port"])
        conn_list = []
        self.game_dict = {}
        self.data = ""
        self.waiting_connection = None
        self.stop = False

        self.server_socket = socket.socket()  # get instance
        # look closely. The bind() function takes tuple as argument
        self.server_socket.bind((host, port))  # bind host address and port together

        # configure how many client the server can listen simultaneously
        self.logger.info("Started listening")
        self.server_socket.listen(3)
        while not self.stop:
            self.logger.info("attempting to accept a connection")
            conn_list = self.accept_conn(conn_list)

        for conn in conn_list:
            conn.close()

    def remove_waiting(self):
        """Set the waiting connection to None to remove it"""
        print("removed waiting")
        self.waiting_connection = None

    def accept_conn(self, conn_list):
        """Accept a connection to the server"""
        conn, address = self.server_socket.accept()  # accept new connection
        self.logger.info("Connection from: %s", str(address))
        conn_type = conn.recv(1024).decode()
        if conn_type == "testing":
            self.logger.warning("STOP COMMAND RECIEVED")
            self.stop = True
        elif conn_type == "testing2":
            self.logger.warning("RESETING SERVER GAMES")
            for conn in conn_list:
                conn.close()
            self.game_dict = {}
            return []
        new_connection = Connection(self, conn, address, 1)
        conn_list.append(new_connection)
        self.connection_game_sort(new_connection)
        return conn_list

    def connection_game_sort(self, connection):
        """Sort connections into games"""
        if self.waiting_connection is None:
            # put player into waiting position
            self.waiting_connection = connection
        else:
            # Create a new game with the new connection and player
            self.waiting_connection.initialize()
            self.logger.info("Creating new game")
            self.game_dict[get_new_id(self.game_dict)] = Game(self, self.waiting_connection,
                                                              connection)

    def append_to_data(self, data):
        """Append the given data to the server's data"""
        self.data += data
        return self.data


def get_new_id(id_dictionary):
    """Get an id that is not in use in the dicitionary"""
    if id_dictionary == {}:
        return 1
    keys = id_dictionary.keys()
    for i in range(1, max(keys)):
        if i not in keys:
            return i
    return max(keys)+1


def setup_logging():
    """Logging for server"""
    log = logging.getLogger('server')
    log.setLevel(logging.INFO)

    if not os.path.exists('logs'):
        os.makedirs('logs')

    file_handler = RotatingFileHandler("./logs/latest.log", mode='a', maxBytes=5*1024*1024,
                                       backupCount=2)

    dt_fmt = '%Y-%m-%d %H:%M:%S'
    fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
    file_handler.setFormatter(fmt)
    log.addHandler(file_handler)

    # Setup logging to the console aswell for quick live debugging
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    log.addHandler(stream_handler)
    # Also want to log to console so add a stream handler too
    return log


if __name__ == '__main__':
    server_object = ServerProgram()
