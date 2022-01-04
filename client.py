"""
Start time = 14:30 Monday 3rd December 2022
Finish time = 02:10 Tuesday 4th December 2022
"""
import random
from game_objects import Board, Display


class Client:
    """Runs the server and display threads"""
    def __init__(self):
        self.board = Board()
        self.display = Display(self, self.board)
        # play_state through 4 modes 1c, 2p, 2c, 1p can start with either 2p or 1p
        self.game_vars = {"play_state": "",
                          "prev_winner": "",
                          "mode": "",
                          "chosen": False,
                          "window_open": True,
                          "chosen_piece": "",
                          "chosen_loc": (0, 0)}

        self.display.display_avaliable()
        self.display.display_menu_input()
        self.display.root.mainloop()

    def set_mode(self, mode):
        """Sets this clients mode to either local or online"""
        self.game_vars["mode"] = mode
        if mode == "Local":
            self.local_play()
        else:
            self.online_play()

    def pick_starter(self):
        """Pick the player who starts if a previous winner did not win"""
        if self.game_vars["prev_winner"] == "":
            self.game_vars["play_state"] = random.choice(["1c", "2c"])

    def local_play(self):
        """Play a local game"""
        self.pick_starter()
        self.display.canvas.delete("player")
        self.display.display_avaliable()
        while self.game_vars["play_state"] != "Finished" and self.game_vars["window_open"]:
            self.local_round()

    def update_window(self):
        """update the display on the window"""
        self.display.root.update()

    def local_round(self):
        """Plays a local round"""
        self.display.setup_binds()
        p = self.game_vars["play_state"][0]
        self.display.set_player_info(f"Player {p} picks a piece for Player {get_other(p)} to play")

        self.choice_wait()
        if not self.game_vars["window_open"]:
            return

        p = self.game_vars["play_state"][0]
        self.display.set_player_info(f"Player {p} select where the piece goes")

        self.choice_wait()
        if not self.game_vars["window_open"]:
            return

        i, j = self.game_vars["chosen_loc"]
        piece = self.game_vars["chosen_piece"]
        self.board.play_move(j, i, piece)
        # Set values back to defaults
        self.game_vars["chosen_loc"] = (0, 0)
        self.game_vars["chosen_piece"] = ""
        self.display.canvas.delete("Mark")

        # update avaliable pieces shown
        self.display.canvas.delete("avaliable")
        self.display.display_avaliable()

        self.display.update_board()
        self.update_window()
        if self.board.check_win():
            self.display.set_player_info(f"Player {p} wins!")
            self.game_vars["play_state"] = "Finished"
            self.display.display_menu_input()
            self.board.reset()
            return

    def choice_wait(self):
        """Wait for the player to make a choice"""
        self.game_vars["chosen"] = False
        while not self.game_vars["chosen"] and self.game_vars["window_open"]:
            # keep board updating
            self.update_window()

    def piece_clicked(self, tag):
        """A piece was clicked"""
        state = self.game_vars["play_state"]
        if state[1] == "c":
            self.display.mark_piece(tag)
            self.game_vars["chosen_piece"] = tag
            self.game_vars["play_state"] = f"{get_other(state[0])}p"
            self.game_vars["chosen"] = True

    def board_clicked(self, tag):
        """Place the previously chosen piece onto the chosen location on the board"""
        i, j = map(int, tag.split("_")[-1].split(","))
        state = self.game_vars["play_state"]
        if state[1] == "p":
            self.game_vars["chosen_loc"] = (i, j)
            self.game_vars["play_state"] = f"{state[0]}c"
            self.game_vars["chosen"] = True

    def online_play(self):
        """Play an online game"""
        self.get_player_name()

    def get_player_name(self):
        """
        Get player's name for online play
        Display input box and enter
        """


def get_other(player):
    """Get the other players number, 1 return 2, 2 return 1"""
    if player in (1, "1"):
        return 2
    return 1


if __name__ == '__main__':
    game_host = Client()
