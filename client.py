"""
Start time = 14:30 Monday 3rd December 2022
Finish time = 02:10 Tuesday 4th December 2022
"""
import random
import socket
import os  # For logging
import logging
import json
from logging.handlers import RotatingFileHandler
from icecream import ic

from game_objects import Board
from display import Display


class Client:
    """Runs the server and display """
    def __init__(self):
        self.logger = setup_logging()
        self.board = Board()
        self.display = Display(self, self.board)
        # play_state through 4 modes 1c, 2p, 2c, 1p can start with either 2p or 1p
        self.display.display_avaliable()
        self.display.display_menu_input()
        self.game_vars = {"open_window": True}
        self.game_client = None
        self.display.root.mainloop()

    def close(self):
        """Close online game client connection"""
        ic(self.game_client)
        if self.game_client:
            self.game_client.close()
        self.game_client = None

    def set_mode(self, mode):
        """Sets this clients mode to either local or online"""
        # Key bind pressed when game already in progress
        ic(mode)
        ic(self.game_client)
        ic(self)
        if self.game_client is not None:
            return
        if mode == "Local":
            self.local_play()
        else:
            self.online_play()

    def local_play(self):
        """Play a local game"""
        self.game_client = LocalPlay(self)
        self.game_client.play_game()
        print("revoked display to main client Local")
        self.display.set_client(self)

    def online_play(self):
        """Play an online game"""
        self.game_client = OnlinePlay(self)
        self.game_client.play_game()
        print("revoked display to main client Online")
        self.display.set_client(self)


class LocalPlay:
    """Play a local game"""
    def __init__(self, client):
        self.client = client
        self.display = client.display
        self.logger = client.logger
        self.display.set_client(self)
        self.board = client.board
        self.game_vars = {"play_state": "",
                          "player": None,
                          "prev_winner": "",
                          "mode": "",
                          "chosen": False,
                          "window_open": True,
                          "chosen_piece": "",
                          "chosen_loc": (None, None)}

    def play_game(self):
        """Play the local game"""
        self.pick_starter()
        self.display.canvas.delete("player")
        self.display.display_avaliable()
        while self.game_vars["play_state"] != "Finished" and self.game_vars["window_open"]:
            self.local_round()

    def close(self):
        """Close the game client"""
        # Not needed for local, but overwritten by online
        # Turns out that isn't used at all currently

    def pick_starter(self):
        """Pick the player who starts if a previous winner did not win"""
        if self.game_vars["prev_winner"] == "":
            state = random.choice(["1c", "2c"])
            self.game_vars["play_state"] = state
            self.game_vars["player"] = state[0]

    def update_window(self):
        """update the display on the window"""
        self.display.root.update()

    def local_round(self):
        """Plays a local round"""
        self.display.setup_binds()
        p = self.game_vars["play_state"][0]
        self.game_vars["player"] = p
        self.display.set_player_info(f"Player {p} picks a piece for Player {get_other(p)} to play")

        self.choice_wait()
        if not self.game_vars["window_open"]:
            return

        p = self.game_vars["play_state"][0]
        self.game_vars["player"] = p
        self.display.set_player_info(f"Player {p} select where the piece goes")

        self.choice_wait()
        if not self.game_vars["window_open"]:
            return
        state = self.game_vars["play_state"]
        self.game_vars["player"] = f"{get_other(state[0])}"

        i, j = self.game_vars["chosen_loc"]
        piece = self.game_vars["chosen_piece"]
        self.board.play_move(j, i, piece)
        # Set values back to defaults
        self.game_vars["chosen_loc"] = (None, None)
        self.game_vars["chosen_piece"] = ""
        self.display.canvas.delete("Mark")

        # update avaliable pieces shown
        self.update_display()

        if self.check_win(p):
            return

    def check_win(self, p, online=False):
        """Check for a winner"""
        if self.board.check_win():
            if online:
                self.display_online_winner(p)
            else:
                self.display.set_player_info(f"Player {p} wins!")
            self.game_vars["play_state"] = "Finished"
            self.client.game_client = None
            ic(self.client.game_client)
            ic(self.client)
            self.display.display_menu_input()
            self.board.reset()
            return True
        return False

    def display_online_winner(self, p):
        """Show if this player won or lost"""
        if p == self.game_vars["player"]:
            self.display.set_player_info("You win!")
            return
        self.display.set_player_info("You Lost :(")

    def update_display(self):
        """Update the display of avaliable pieces"""
        self.display.canvas.delete("avaliable")
        self.display.display_avaliable()

        self.display.update_board()
        self.update_window()

    def choice_wait(self):
        """Wait for the player to make a choice"""
        self.game_vars["chosen"] = False
        while not self.game_vars["chosen"] and self.game_vars["window_open"]:
            # keep board updating
            self.update_window()

    def piece_clicked(self, tag):
        """A piece was clicked"""
        state = self.game_vars["play_state"]
        ic(state)
        if state[1] == "c" and self.check_selecting():
            self.display.mark_piece(tag)
            self.game_vars["chosen_piece"] = tag
            self.game_vars["play_state"] = f"{get_other(state[0])}p"
            self.game_vars["chosen"] = True

    def check_selecting(self):
        """Check if the current player should be selecting"""
        state = self.game_vars["play_state"]
        player = self.game_vars["player"]
        if state[0] == player:
            return True
        return False

    def board_clicked(self, tag):
        """Place the previously chosen piece onto the chosen location on the board"""
        i, j = map(int, tag.split("_")[-1].split(","))
        state = self.game_vars["play_state"]
        ic(state)
        if state[1] == "p":
            self.game_vars["chosen_loc"] = (i, j)
            self.game_vars["play_state"] = f"{state[0]}c"
            self.game_vars["chosen"] = True


class OnlinePlay(LocalPlay):
    """Client for hosting online play"""
    def __init__(self, client):
        super().__init__(client)
        self.client_socket = None
        with open("config.json", "r") as f:
            config = json.load(f)
        self.conn_vars = {"host": config["host"],
                          "port": int(config["port"]),
                          "connected": False}

    def play_game(self):
        # Create a TCP/IP socket
        self.establish_connection()
        # Kick off the game running
        self.run()

    def run(self):
        """Run the online program"""
        initial_data = self.recv()
        # Game closed if data is none so return this thread to stop error
        print(f"initial_data {initial_data}")
        ic(initial_data)
        if not initial_data or not self.game_vars["window_open"]:
            return
        split_data = initial_data.split(",")
        player = split_data[0]
        first = split_data[1]

        self.game_vars["player"] = player
        self.game_vars["play_state"] = f"{first}c"
        self.online_round()

    def online_round(self):
        """Plays out an online round"""
        # first move is special case then rest is a 2 part loop
        # pick piece
        self.update_display()
        self.display.setup_binds()
        # delete possible pieces from previous game
        self.display.canvas.delete("player")
        # Update the displayed avaliable pieces
        ic("1online_round", self.game_vars["player"], self.game_vars["play_state"])
        self.piece_selection()
        if not self.game_vars["window_open"]:
            return

        while self.game_vars["play_state"] != "Finished" and self.game_vars["window_open"]:
            # loop till done
            # play piece
            ic("2online_round", self.game_vars["player"], self.game_vars["play_state"])
            self.play_piece()

            if self.check_win(self.game_vars["play_state"][0], online=True):
                return

            if not self.game_vars["window_open"]:
                return
            # pick piece
            ic("3online_round", self.game_vars["player"], self.game_vars["play_state"])
            self.display.setup_binds()
            self.piece_selection()
            if not self.game_vars["window_open"]:
                return

    def play_piece(self):
        """Selected piece needs to be played"""
        ic("play_piece", self.game_vars["player"], self.game_vars["play_state"])
        if self.game_vars["player"] == self.game_vars["play_state"][0]:
            self.player_plays_piece()
        else:
            self.player_location_choice_wait()

        if not self.game_vars["window_open"]:
            return

        self.play_move()
        self.update_display()

    def player_location_choice_wait(self):
        """Wait for the other player to choose where the piece goes"""
        p = self.game_vars["player"]
        self.display.set_player_info(f"Wait for Player {get_other(p)} to pick a location")

        # Send some random data to tell the server that wait is ready
        self.send("waiting")

        location = self.recv()
        if not self.game_vars["window_open"]:
            return
        self.game_vars["chosen_loc"] = parse_loc(location)

    def player_plays_piece(self):
        """Player selects where the piece goes on the board"""
        self.display.set_player_info("Pick where the piece goes")

        self.choice_wait()
        if not self.game_vars["window_open"]:
            return
        loc = self.game_vars["chosen_loc"]
        self.send(loc)
        print("send loc")
        # Wait for the server to confirm
        loc = self.recv()
        print("recieved loc back")
        loc = parse_loc(loc)
        ic(loc, self.game_vars["chosen_loc"])
        if loc != self.game_vars["chosen_loc"]:
            self.logger.warning("Mismatch of sent and recieved piece!!")

    def play_move(self):
        """Play the move that was selected by the player"""
        i, j = self.game_vars["chosen_loc"]
        piece = self.game_vars["chosen_piece"]
        self.board.play_move(j, i, piece)
        # Set values back to defaults
        self.game_vars["chosen_loc"] = None
        self.game_vars["chosen_piece"] = ""
        self.display.canvas.delete("Mark")

    def piece_selection(self):
        """Player who's turn it is to pick picks a piece"""
        state = self.game_vars["play_state"]
        if self.game_vars["player"] == state[0]:
            self.player_picks()
        else:
            self.player_piece_choice_wait()
        if not self.game_vars["window_open"]:
            return
        state = f"{get_other(state[0])}p"
        self.game_vars["play_state"] = state
        print(f"Changed state to {state}")

    def player_picks(self):
        """This player is picking the piece"""
        p = self.game_vars["player"]
        self.display.set_player_info(f"Pick a piece for Player {get_other(p)} to play")

        # Wait for this player to make a choice
        self.choice_wait()

        if not self.game_vars["window_open"]:
            return
        self.send(self.game_vars["chosen_piece"])
        print("sent choice")
        # Even if the player picked need to have both clients send and recieve synced
        piece = self.recv()
        print("recieved confirm")
        print("piece", piece)
        print("saved piece", self.game_vars["chosen_piece"])
        if piece != self.game_vars["chosen_piece"]:
            self.logger.warning("Mismatch of sent and recieved piece!!")

    def player_piece_choice_wait(self):
        """This player is waiting for the other to pick"""
        p = self.game_vars["player"]
        self.display.set_player_info(f"Wait for Player {get_other(p)} to pick a piece")

        # Send some random data to tell the server that wait is ready
        self.send("waiting")

        piece = self.recv()
        if not self.game_vars["window_open"]:
            return
        self.game_vars["chosen_piece"] = piece
        self.display.mark_piece(piece)

    def recv(self):
        """Recieve data from the server"""
        data = None
        while not data and self.game_vars["window_open"]:
            try:
                data = self.client_socket.recv(1024).decode()
            except socket.timeout:
                data = None
            self.display.root.update()
        return data

    def send(self, data):
        """Send data to the server"""
        ic(f"sending data {data}")
        self.client_socket.send(str(data).encode())

    def establish_connection(self):
        """Establish a connection between the server and the client"""
        # Immediatly start trying to connect
        self.display.set_player_info("Attempting to connect...")
        self.connect()
        if not self.conn_vars["connected"] and self.game_vars["window_open"]:
            # When reattempting to connect wait 5 seconds before retrying
            self.display.set_player_info("Failed to connect...")
            self.display.call_after(5, self.establish_connection)
            return
        self.display.clear_menu()
        self.display.set_player_info("Successfully connected...")
        # self.display.call_after(5, lambda: self.display.set_player_info("Waiting for other "
        #                                                                 "players..."))

    def connect(self):
        """Connect to the host"""
        self.client_socket = socket.socket()
        # self.client_socket.setblocking(False)
        host = self.conn_vars["host"]
        port = self.conn_vars["port"]
        try:
            ic(host, port)
            self.client_socket.connect((host, port))
            self.client_socket.send("client".encode())
        except ConnectionRefusedError:
            self.conn_vars["connected"] = False
            print("Connection refused")
        else:
            self.conn_vars["connected"] = True
            # Set timeout to a short time to allow for waiting
            self.client_socket.settimeout(0.1)
            print("Sucessfully connected")


def get_other(player):
    """Get the other players number, 1 return 2, 2 return 1"""
    if player in (1, "1"):
        return 2
    return 1


def setup_logging():
    """Logging for server"""
    log = logging.getLogger('client')
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


def parse_loc(loc):
    """Parse from string to tuple"""
    return tuple(map(int, loc[1:-1].split(", ")))


if __name__ == '__main__':
    game_host = Client()
