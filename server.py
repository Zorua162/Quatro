"""Start time = 14:30"""
import socket
import random
import threading
from game_objects import Board


class Player:
    """Stores information about a player"""
    def __init__(self, conn, address, name, player_number):
        self.conn = conn
        self.address = address
        self.name = name
        self.player_number = player_number


class Game:
    """Hosts the game elements"""
    def __init__(self, player1, player2):
        self.board = Board()
        self.play_state = pick_starter()
        self.player1 = player1
        self.player2 = player2
        self.game_thread = threading.Thread(target=self.start)

    def start(self):
        """Start the game running"""
        print("Started thread" + self.game_thread)


class Server:
    """The host server for the game"""
    def __init__(self):
        self.host_name = socket.gethostname()
        self.port = 5000  # initiate port no above 1024
        self.server_socket = socket.socket()  # get instance
        # look closely. The bind() function takes tuple as argument
        self.server_socket.bind((self.host_name, self.port))  # bind host address and port together

        self.game_list = {}

        self.pending_player = ""

        # configure how many client the server can listen simultaneously
        self.server_socket.listen(2)

        # recv data = conn.recv(1024).decode()
        # send conn.send(data.encode())  # send data to the client

        while True:
            conn, address = self.server_socket.accept()  # accept new connection
            print("Connection from: " + str(address))

            if self.pending_player == "":
                conn.send("Player 1 waiting for others".encode())  # send data to the client
                self.pending_player = Player(conn, address, "Name", 1)
            else:
                game = self.add_game(conn, address)
                game.start()

            # receive data stream. it won't accept data packet greater than 1024 bytes
            data = conn.recv(1024).decode()
            print("from connected user: " + str(data))
            data = input(' -> ')
            conn.send(data.encode())  # send data to the client

        conn.close()  # close the connection

    def add_game(self, conn, address):
        """Add a game to the game_list"""
        new_game = Game(self.pending_player, Player(conn, address, "Name2", 1))
        if self.game_list == {}:
            self.game_list[0] = new_game
        else:
            self.game_list[max(self.game_list.values())+1] = new_game
        return new_game


def pick_starter():
    """Pick which player starts randomly"""
    return random.choice(["1c", "2c"])


if __name__ == '__main__':
    server = Server()
