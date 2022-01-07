"""Objects required for the quatro game"""

ATTRS = ["tall", "black", "round", "hollow"]
INVS_ATTRS = {"tall": "short", "black": "white", "round": "square", "hollow": "full"}


class Piece:
    """Represents a piece"""
    def __init__(self, bin_rep):
        self.attr_dict = {attr: (bool(bin_rep[i] == '1')) for i, attr in enumerate(ATTRS)}
        self.size = 10
        self.turn = 2
        self.bin = bin_rep

        if self.attr_dict["black"]:
            self.fill = "black"
            self.outline = "white"
        else:
            self.fill = "white"
            self.outline = "black"

        if self.attr_dict["tall"]:
            self.height = 20
        else:
            self.height = 10

    def draw(self, canvas, location, tag="player"):
        """Draw the piece on a given canvas"""
        if self.attr_dict["round"]:
            self.draw_round(canvas, location, tag)
        else:
            self.draw_square(canvas, location, tag)
        return self.bin

    def draw_round(self, canvas, location, tag):
        """Draw round piece on a given canvas"""
        centerx, centery = location
        canvas.create_oval(centerx-self.size, centery-self.size+self.turn,
                           centerx+self.size, centery+self.size-self.turn,
                           fill=self.fill,
                           outline=self.outline, tags=(tag, self.bin))

        canvas.create_rectangle(centerx-self.size, centery,
                                centerx+self.size, centery-self.height,
                                fill=self.fill,
                                outline=self.fill, tags=(tag, self.bin))

        canvas.create_line(centerx-self.size, centery,
                           centerx-self.size, centery-self.height,
                           fill=self.outline, tags=(tag, self.bin))

        canvas.create_line(centerx+self.size, centery,
                           centerx+self.size, centery-self.height,
                           fill=self.outline, tags=(tag, self.bin))

        canvas.create_oval(centerx-self.size, centery-self.size+self.turn-self.height,
                           centerx+self.size, centery+self.size-self.turn-self.height,
                           fill=self.fill,
                           outline=self.outline, tags=(tag, self.bin))

        if self.attr_dict["hollow"]:
            canvas.create_oval(centerx-self.size/2, centery-self.size/2+self.turn/2-self.height,
                               centerx+self.size/2, centery+self.size/2-self.turn/2-self.height,
                               fill=self.fill,
                               outline=self.outline, tags=(tag, self.bin))

    def draw_square(self, canvas, location, tag):
        """Draw a square piece on a given canvas"""
        centerx, centery = location
        # Create main rectangle cuboid shape
        canvas.create_polygon(centerx, centery+self.size-self.turn,
                              centerx-self.size, centery,
                              centerx-self.size, centery-self.height,
                              centerx, centery-self.height-self.size+self.turn,
                              centerx+self.size, centery-self.height,
                              centerx, centery-self.height+self.size-self.turn,
                              centerx-self.size, centery-self.height,
                              centerx, centery-self.height+self.size-self.turn,
                              centerx+self.size, centery-self.height,
                              centerx+self.size, centery,
                              centerx, centery+self.size-self.turn,
                              centerx, centery-self.height+self.size-self.turn,
                              fill=self.fill,
                              outline=self.outline, tags=(tag, self.bin))

        # create cutout for hollow if hollow
        if self.attr_dict["hollow"]:
            canvas.create_polygon(centerx, centery-self.height-self.size/2+self.turn/2,
                                  centerx-self.size/2, centery-self.height,
                                  centerx, centery-self.height+self.size/2-self.turn/2,
                                  centerx+self.size/2, centery-self.height,
                                  centerx, centery-self.height-self.size/2+self.turn/2,
                                  centerx, centery-self.height+self.size/2-self.turn/2,
                                  fill=self.fill,
                                  outline=self.outline, tags=(tag, self.bin))

    def add_to_attr_count(self, attr_count):
        """Adds all the piece's attrs to the attr_count"""
        for attr in ATTRS:
            if self.attr_dict[attr]:
                attr_count[attr] += 1
            else:
                attr_count[INVS_ATTRS[attr]] += 1

        return attr_count


class Board:
    """The main game board"""
    def __init__(self):
        self.unplayed_pieces = [f'{i:0>4b}' for i in range(0, 16)]
        # Board it rotated 45 degrees clockwise
        # so the first index is the right diagonal and second left
        self.r_len = 4
        self.game_board = [[0 for j in range(0, self.r_len)] for i in range(0, self.r_len)]

    def reset(self):
        """Reset the game board"""
        self.unplayed_pieces = [f'{i:0>4b}' for i in range(0, 16)]
        self.game_board = [[0 for j in range(0, self.r_len)] for i in range(0, self.r_len)]

    def get_board(self):
        """Get the board array"""
        return self.game_board

    def play_move(self, x, y, bin_rep):
        """Play a piece on the board"""
        self.game_board[y][x] = Piece(bin_rep)
        self.unplayed_pieces.remove(bin_rep)

    def check_win(self):
        """Check if a win condition has been met on the board
        i.e that 4 of the same attribute in row
        """
        attr_count = {"tall": 0, "short": 0,
                      "square": 0, "round": 0,
                      "black": 0, "white": 0,
                      "full": 0, "hollow": 0}
        possible_list = []
        possible_list.extend([[(i, j) for i in range(0, self.r_len)] for j in range(0, self.r_len)])
        possible_list.extend([[(j, i) for i in range(0, self.r_len)] for j in range(0, self.r_len)])
        possible_list.extend([[(i, i) for i in range(0, self.r_len)]])
        possible_list.extend([[(i, self.r_len-1-i) for i in range(0, self.r_len)]])
        for row in possible_list:
            current_attr_count = attr_count.copy()
            for pos in row:
                piece = self.game_board[pos[0]][pos[1]]
                if not isinstance(piece, int):
                    current_attr_count = piece.add_to_attr_count(current_attr_count)
            for _, value in current_attr_count.items():
                if value >= 4:
                    return True
        return False
