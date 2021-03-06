"""For doing all the program's display"""
import tkinter as tk

from game_objects import Piece


class Display:
    """Display the GUI to the users"""
    def __init__(self, client, board):
        self.client = client
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, height=400, width=800)
        self.canvas.pack()

        canvas_width = self.canvas.winfo_reqwidth()
        canvas_height = self.canvas.winfo_reqheight()
        self.canvas_dims = canvas_width, canvas_height

        self.board = board
        self.root.bind("q", self.close)
        # index_map in the form (i, j), to coordiantes of form (x, y)
        index_map = {}
        avaliable_map = {}
        self.maps = {"index_map": index_map, "avaliable_map": avaliable_map}

        self.canvas.create_text(canvas_width/2, 20, text="Quatro",
                                font=("Consolas", "30"))
        self.player_info = self.canvas.create_text(canvas_width/2, 50,
                                                   text="Waiting for players...",
                                                   font=("Consolas", "20"))
        self.display_game_board()
        self.root.update()

    def close(self, _):
        """Close the window"""
        self.set_game_var("window_open", False)
        self.client.close()
        self.root.after(1, self.root.destroy)

    def set_game_var(self, var, value):
        """Set a value in the game_vars"""
        self.get_game_vars()[var] = value

    def get_game_vars(self):
        """Get the game vars"""
        return self.client.game_vars

    def set_client(self, client):
        """Set the current client that is controlling the display"""
        self.client = client

    def display_game_board(self):
        """Display the current board with tkinter"""
        self.canvas.delete("board")
        r = 15
        stepx = r*2
        stepy = r*2
        canvas_width, canvas_height = self.canvas_dims
        starty = canvas_height/2 - 3*stepy - stepy*2
        startx = canvas_width/2

        game_board = self.board.get_board()
        for i, line in enumerate(game_board):
            starty += stepy
            startx += stepx
            y = starty
            x = startx
            for j, _ in enumerate(line):
                x -= stepx
                y += stepy
                self.canvas.create_oval(x-r, y-r, x+r, y+r,
                                        tags=("board", f"board_{i},{j}"), fill="gray")
                self.maps["index_map"][(i, j)] = (x, y)

    def update_board(self):
        """update the shown pieces on the board"""
        game_board = self.board.get_board()
        for i, line in enumerate(game_board):
            for j, piece in enumerate(line):
                if not isinstance(piece, int):
                    piece.draw(self.canvas, self.maps["index_map"][(i, j)])

    def display_avaliable(self):
        """Display the pieces that are avaliable on the left and right of the board"""
        il = 0
        jl = 0
        ir = 0
        jr = 0
        height_offset = 100
        width_offset = 100
        canvas_width = self.canvas_dims[0]
        stepx = 40
        stepy = 40
        for i in range(0, 16):
            piece = f'{i:0>4b}'
            if piece[1] == "1":
                if piece in self.board.unplayed_pieces:
                    pos = (jl+width_offset, il+height_offset)
                    Piece(piece).draw(self.canvas, pos, "avaliable")
                    self.maps["avaliable_map"][piece] = pos
                jl += stepx
                if jl >= 2*stepx:
                    jl = 0
                    il += stepy
            else:
                if piece in self.board.unplayed_pieces:
                    pos = (canvas_width-(jr+width_offset), (ir+height_offset))
                    Piece(piece).draw(self.canvas, pos, "avaliable")
                    self.maps["avaliable_map"][piece] = pos
                jr += stepx
                if jr >= 2*stepx:
                    jr = 0
                    ir += stepy

        self.update_board()

    def mark_piece(self, piece):
        """Put a ring around a piece that has been selected"""
        x, y = self.maps["avaliable_map"][piece]
        r = 15
        self.canvas.create_oval(x+r, y+r, x-r, y-r, tag="Mark")
        self.canvas.tag_lower("Mark")

    def display_menu_input(self):
        """Gets if the player would like to play locally or online"""
        canvas_width, canvas_height = self.canvas_dims
        width = canvas_width/8
        height = canvas_height/8
        self.canvas.create_rectangle(canvas_width/4-width, 3*canvas_height/4-height,
                                     canvas_width/4+width, 3*canvas_height/4+height,
                                     fill="gray", tag="Local")

        self.canvas.create_rectangle(3*canvas_width/4-width, 3*canvas_height/4-height,
                                     3*canvas_width/4+width, 3*canvas_height/4+height,
                                     fill="gray", tag="Online")

        self.canvas.create_text(canvas_width/4, 3*canvas_height/4,
                                text="Local", font=("Consolas", "30"), tag="Local")

        self.canvas.create_text(3*canvas_width/4, 3*canvas_height/4,
                                text="Online", font=("Consolas", "30"), tag="Online")

        self.canvas.tag_bind("Local", '<ButtonPress-1>', lambda mode: self.set_mode("Local"))
        self.canvas.tag_bind("Online", '<ButtonPress-1>', lambda mode: self.set_mode("Online"))
        self.root.bind("a", lambda mode: self.set_mode("Local"))
        self.root.bind("d", lambda mode: self.set_mode("Online"))

    def setup_binds(self):
        """Setup the binding to the avaliable pieces"""
        for item_id in self.canvas.find_all():

            tags = self.canvas.gettags(item_id)
            if len(tags) > 1:
                tag = tags[1]
                if tag in self.board.unplayed_pieces:
                    self.canvas.tag_bind(item_id, '<Button-1>',
                                         lambda _, t=tag: self.client.piece_clicked(t))
                elif "board" in tag:
                    self.canvas.tag_bind(item_id, '<Button-1>',
                                         lambda _, t=tag: self.client.board_clicked(t))

    def set_mode(self, mode):
        """Set the mode"""
        if mode == "Local":
            self.clear_menu()
        self.client.set_mode(mode)

    def clear_menu(self):
        """Clear the menu of buttons"""
        self.canvas.delete("Local", "Online")

    def set_player_info(self, text):
        """Sets the player info text to contain "text"

        :text: @todo
        :returns: @todo

        """
        self.canvas.itemconfig(self.player_info, text=text)
        self.root.update()

    def call_after(self, delay, func):
        """Call then given function after some time using the .after function"""
        self.root.after(delay*1000, func)
