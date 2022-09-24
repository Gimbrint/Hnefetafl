from enum import IntEnum
from sys import argv
import pygame
import math

class Hnefetafl:
	def __init__(self, whiteToMove : bool, sprite_storage, fen : str, width : int=11, height : int=11) -> None:
		self.width = width
		self.twidth = width + 2 # Total num of columns, including imaginary columns
		self.height = height
		self.size = width * height
		self.tsize = self.twidth * height

		self.directions : list = [self.twidth, -self.twidth, 1, -1]
		self.move_dirs : list = [[list for y in range(4)] for x in range(self.size)]
		self.calculate_move_dirs()

		# | enemy pieces nearby (x (00), y (00)) | pos | color | type |
		#			0000 000000 00 00
		self.colorMask = 3 << 2

		# Settings
		self.edge_attacks = True
		self.long_moves = True
		self.throne_enabled = True

		self.has_king = False
		self.who_won : str

		# Window
		self.screenX : int = 800 #1024
		self.screenY : int = 800 #600
		self.screen = pygame.display.set_mode((self.screenX, self.screenY))
		
		# Used for square generating
		self.chosen_size = min(self.screenX, self.screenY) / max(width, height)
		self.chosen_size /= max(self.chosen_size * width / self.screenX, self.chosen_size * height / self.screenY)
		self.base_offset_x = (self.screenX - self.chosen_size * self.width) / 2
		self.base_offset_y = (self.screenY - self.chosen_size * self.height) / 2

		self.sprites : self.sprite_storage = sprite_storage
		self.resize_sprites(self.sprites)

		# Test stuff
		self.fen = fen
		self.restart_game()
		#self.make_move(self.move(0, 8))
		#self.make_move(self.move(2, 10))
		self.log_board(self.board, self.twidth, self.height)

		pygame.init()

		# Closing loop
		selected_piece = None
		visual_start_pos = 0
		held_down = False
		running = True

		while running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
					pygame.quit()
					import sys
					sys.exit(0)
				if self.current_state == self.game_state.RUNNING:
					if event.type == pygame.MOUSEBUTTONDOWN: # Select piece
						mousePos = pygame.mouse.get_pos()

						if self.is_mouse_inside_board(mousePos):
							selected_pos = self.get_mouse_to_board_pos(mousePos)

							if self.board[selected_pos] != None and self.board[selected_pos].color_index == self.friendlyColorIndex:
								held_down = True

								selected_piece = self.board[selected_pos]
								visual_start_pos = selected_piece.visual_pos
								print("Start")
					if event.type == pygame.MOUSEBUTTONUP: # Drop piece
						if selected_piece != None:
							held_down = False
								
							self.board[selected_piece.pos].visual_pos = visual_start_pos
							mousePos = pygame.mouse.get_pos()

							if self.is_mouse_inside_board(mousePos):
								for i in range(0, len(self.moves[selected_piece.color_index])):
									move = self.moves[selected_piece.color_index][i]

									if move.startPos == selected_piece.pos and move.targetPos == self.get_mouse_to_board_pos(mousePos):
										self.make_move(move)
										break

							selected_piece = None
							print("YES!!!")
					if held_down and selected_piece != None: # Drag piece
						mousePos = pygame.mouse.get_pos()
						selected_piece.visual_pos = (mousePos[0] - self.chosen_size / 2, mousePos[1] - self.chosen_size / 2)
				else:
					if event.type == pygame.KEYDOWN:
						if event.key == pygame.K_r:
							self.restart_game()

			# Background color
			background_color = (255, 255, 255)
			self.screen.fill(background_color)

			if self.current_state == self.game_state.RUNNING:
				# Generate squares
				for x in range(width):
					for y in range(height):
						pos = y * self.twidth + x

						if self.is_edge_square(pos):
							self.screen.blit(self.sprites.square_sprites[2], self.board_to_visual_pos(pos))
						elif pos == self.throne:
							# This is kinda stupid, but i don't know how i would like to fix this
							self.screen.blit(self.sprites.square_sprites[3], self.board_to_visual_pos(pos))
						else:
							self.screen.blit(self.sprites.square_sprites[1 - ((x + y) & 1)], self.board_to_visual_pos(pos))

				# Generate move squares
				for i in range(0, len(self.moves[self.friendlyColorIndex]), 1):
					self.screen.blit(self.sprites.move_sprite, self.board_to_visual_pos(self.moves[self.friendlyColorIndex][i].targetPos))

				# Generate pieces
				for i in range(0, len(self.pieces), 1):
					for j in range(len(self.pieces[i])):
						piece = self.board[self.pieces[i][j]]

						# Kinda scuffed, but works!
						if selected_piece != None and piece.pos == selected_piece.pos:
							continue
						
						self.screen.blit(self.sprites.piece_sprites[piece.color_index * 2 + piece.piece_type - 1], piece.visual_pos)

				# Generate selected piece
				if selected_piece != None:
					self.screen.blit(self.sprites.piece_sprites[selected_piece.color_index * 2 + selected_piece.piece_type - 1], selected_piece.visual_pos)
			else:
				# NOTE: Win screen
				# Win text
				self.draw_text(self.who_won + " has won", (self.screenX >> 1, self.screenY / 2.7), int(self.screenX / 12))
				self.draw_text("Press R to restart", (self.screenX >> 1, self.screenY / 1.8), int(self.screenX / 20))

			pygame.display.flip()

	def draw_text(self, text : str, pos : tuple[int, int], size : int, color : tuple[int, int, int]=(0, 0, 0)):
		font = pygame.font.SysFont(None, size)
		font_size = font.size(text)
		img = font.render(text, True, color)
		self.screen.blit(img, (pos[0] - (font_size[0] >> 1), pos[1] - (font_size[1] >> 1)))

	def gen_moves(self, isLong : bool=False) -> list:
		self.moves = [list() for x in range(2)]

		for j in range(0, len(self.pieces[self.friendlyColorIndex]), 1):
			piece = self.board[self.pieces[self.friendlyColorIndex][j]]
			board_pos = self.convert_to_board_pos(piece.pos)

			for k in range(0, len(self.directions), 1):
				times = min(self.move_dirs[board_pos][k], 1)
				if isLong:
					times = self.move_dirs[board_pos][k]

				for h in range(0, times, 1):
					targetPos = piece.pos + self.directions[k] * (h + 1)

					# Square must be empty, and if not king check if it's an edge square
					if self.board[piece.pos + self.directions[k] * (h + 1)] == None and (piece.piece_type == self.piece_type.KING or not self.is_edge_square(targetPos)) and piece.piece_type == self.piece_type.KING or targetPos != self.throne:
						move = self.move(piece.pos, targetPos)
						move.set_visual_pos(self)

						self.moves[self.friendlyColorIndex].append(move)
					else:
						break

	def load_from_position(self, notation : str) -> None:
		piece_type_from_symbol : dict = {
			'k': self.piece_type.KING, 'p': self.piece_type.PAWN
		}

		data = notation.split(' ')

		# Check if we have the correct number of chunks
		chunks = 5
		assert len(data) == chunks, "[ERROR] Num of arguments in notation must be exactly: " + str(chunks)

		file : int = 0
		rank : int = self.height - 1

		for i in range(0, len(data[0]), 1):
			symbol = data[0][i]

			if symbol == '/':
				file = 0
				rank -= 1
			else:
				# Check if outside boundaries
				assert file < self.width and rank < self.height, "[ERROR] Error after: " + str(symbol) + " | at: " + str((file, rank)) + "\n\nWhen loading a position, you must stay inside the board boundaries, Width: " + str(self.width) + " | Height: " + str(self.height)

				if symbol.isnumeric():
					file += int(symbol)
				else:
					color_type = self.piece_type.BLACK
					if symbol.upper() == symbol:
						color_type = self.piece_type.WHITE

					type = piece_type_from_symbol[symbol.lower()]

					if type == self.piece_type.KING:
						if not self.has_king:
							self.has_king = True

							if self.throne_enabled and self.throne == -1:
								self.throne = rank * self.twidth + file
								self.throne_color_index = color_type >> 3
						else:
							assert False, "[ERROR] Can't have more than 1 king"

					self.add_piece(rank * self.twidth + file, type | color_type)
					file += 1

		# Color to move implementation
		if data[1].lower() == 'b':
			self.set_to_move_color(False)
		elif data[1].lower() == 'w':
			self.set_to_move_color(True)
		else:
			assert False, "[ERROR] First to move must be either white 'w' or black 'b'"

		# Long moves
		if data[2] == "1":
			self.long_moves = True
		elif data[2] == "0":
			self.long_moves = False
		else:
			assert False, "[ERROR] Long moves must be either 1 (on) or 0 (off)"

		# Throne enabled
		if data[3] == "1":
			self.throne_enabled = True
		elif data[3] == "0":
			self.throne_enabled = False
		else:
			assert False, "[ERROR] Throne must be either 1 (on) or 0 (off)"
		
		# Edge attacks
		if data[4] == "1":
			self.edge_attacks = True
		elif data[4] == "0":
			self.edge_attacks = False
		else:
			assert False, "[ERROR] Edge attacks must be either 1 (on) or 0 (off)"

	def set_to_move_color(self, whiteToMove : bool) -> None:
		self.whiteToMove = True
		self.friendlyColorIndex = int(whiteToMove)
		self.opponentColorIndex = 1 - self.friendlyColorIndex

	def add_piece(self, pos : int, type : int) -> None:
		self.board[pos] = self.Piece(pos=pos, type=type)
		self.board[pos].visual_pos = self.board_to_visual_pos(pos)
		self.pieces[((type & self.colorMask) >> 2) - 1].append(pos)

	def capture_piece(self, pos : int) -> None:
		if self.board[pos].piece_type == self.piece_type.KING:
			# We have captured the opponent's king, and so we have won
			self.end_game(self.friendlyColorIndex)

		self.pieces[self.board[pos].color_index].remove(pos)
		self.board[pos] = None

	def end_game(self, color_index : int) -> None:
		self.current_state = self.game_state.END

		# Who won
		if color_index:
			self.who_won = "White"
		else:
			self.who_won = "Black"

		#self.restart_game()

	def restart_game(self) -> None:
		# Clear board and load new
		self.board = [None for x in range(self.size << 1)]
		self.throne = -1
		self.has_king = False
		self.pieces = [list() for x in range(2)]
		self.moves = [list() for x in range(2)]
		self.load_from_position(self.fen)
		self.calculate_attack_squares()
		self.gen_moves(self.long_moves)

		# Set current game state to running
		self.current_state = self.game_state.RUNNING

	def start_new_round(self) -> None:
		self.whiteToMove = not self.whiteToMove
		self.friendlyColorIndex = self.opponentColorIndex
		self.opponentColorIndex = 1 - self.friendlyColorIndex

		self.calculate_attack_squares()
		self.gen_moves(self.long_moves)

	# Makes a move on the board
	def make_move(self, move) -> None:
		print(self.is_inside_board(move.targetPos))
		if self.board[move.startPos] != None and self.board[move.targetPos] == None and self.is_inside_board(move.targetPos):
			piece : self.Piece = self.board[move.startPos]

			# Remove old pos
			self.board[move.startPos] = None
			self.pieces[piece.color_index].remove(move.startPos)

			# Add new pos
			piece.pos = move.targetPos
			piece.visual_pos = self.board_to_visual_pos(move.targetPos)
			piece.reset_attacked()
			self.board[move.targetPos] = piece
			self.pieces[piece.color_index].append(move.targetPos)

			# Check if there are enemy pieces on the target pos, if so, we attack them and they attact us, also skip this if we are a king
			if not piece.piece_type == self.piece_type.KING and len(self.attackBoard[move.targetPos]) > 0:
				for i in range(0, len(self.attackBoard[move.targetPos]), 1):
					data = self.attackBoard[move.targetPos][i]
					pos = data >> 1
					isX = data & 1

					op_piece = self.board[pos]

					if not (op_piece.color_index == piece.color_index):
						# Attack the piece
						op_piece.attacked += 1 << (isX << 1)
						
						if op_piece.piece_type == self.piece_type.KING: # King capture (2x and 2y)
							if ((op_piece.attacked >> 2) & 3) >= 2 and (op_piece.attacked & 3) >= 2:
								self.capture_piece(pos)
						elif ((op_piece.attacked >> 2 * isX) & 3) >= 2: # Pawn Capture: 2(x or y)
							self.capture_piece(pos)

			if self.is_edge_square(move.targetPos):
				# TODO: Implement end game
				self.end_game(self.friendlyColorIndex)
			else:
				# Now it's the opponent's turn!
				self.start_new_round()

			self.log_board(self.board, 5, 3)

	def calculate_move_dirs(self) -> None:
		for i in range(0, len(self.move_dirs), 1):
			y = int(i / self.
			width)
			x = i - y * self.width

			self.move_dirs[i][0] = self.height - 1 - y
			self.move_dirs[i][1] = y
			self.move_dirs[i][2] = self.height - 1 - x
			self.move_dirs[i][3] = x

	def calculate_attack_squares(self) -> None:
		self.attackBoard = [list() for x in range(self.tsize)]
		opponentPieces : list = self.pieces[self.opponentColorIndex]

		for i in range(0, len(opponentPieces), 1):
			op_piece = self.board[opponentPieces[i]]
			op_piece.reset_attacked()

			for j in range(0, len(self.directions), 1):
				targetHex = opponentPieces[i] + self.directions[j]
				isX = j > 1

				if self.is_inside_board(targetHex):
					if self.is_edge_square(targetHex) and self.edge_attacks:
						# This is an edge square, and so we are attacked by it
						op_piece.attacked += (1 << (isX << 1))
					elif self.throne_enabled and targetHex == self.throne:
						if (self.board[self.throne] == None and op_piece.color_index == self.throne_color_index) or op_piece.color_index != self.throne_color_index:
							# If we are next to the throne and we are the attacker, we are attacked, else if the throne is empty we are also attacked
							op_piece.attacked += (1 << (isX << 1))
					else:
						if not self.board[targetHex] == None:
							if not self.board[targetHex].color_index == self.board[opponentPieces[i]].color_index and not self.board[targetHex].piece_type == self.piece_type.KING:
								# If the opponent's piece is not a king, we are being attacked
								op_piece.attacked += (1 << (isX << 1))

						# Add this attack to the attack board
						self.attackBoard[targetHex].append((opponentPieces[i] << 1) | (j > 1))
				elif op_piece.piece_type == self.piece_type.KING:
					# If we are a king the border attacks us!
					op_piece.attacked += (1 << (isX << 1))
	
	def convert_to_board_pos(self, pos : int):
		return pos - (int(pos / self.twidth) << 1)

	def is_inside_board(self, pos : int) -> bool:
		return pos >= 0 and pos < self.tsize and (pos % self.twidth) < self.width

	def is_edge_square(self, pos : int) -> bool:
		return pos == 0 or pos == self.width - 1 or pos == self.twidth * (self.height - 1) or pos == self.twidth * self.height - 3

	def is_mouse_inside_board(self, pos : tuple[int, int]) -> bool:
		board_pos_x = pos[0] - self.base_offset_x
		board_pos_y = pos[1] - self.base_offset_y

		if board_pos_x < 0 or board_pos_y < 0 or board_pos_x > self.chosen_size * self.width or board_pos_y > self.chosen_size * self.height:
			return False
		return True

	def get_mouse_to_board_pos(self, pos : tuple[int, int]) -> int:
		x = math.floor((pos[0] - self.base_offset_x) / self.chosen_size)
		y = math.floor((self.screenY - self.base_offset_y - pos[1] - self.base_offset_y) / self.chosen_size)
		return y * self.twidth + x

	def log_board(self, board : list, width : int, height : int) -> None:
		if height < 0:
			return

		for y in range(height - 1, -1, -1):
			output = ""

			for x in range(0, width, 1):
				output += str(y * width + x) + " | " + board[y * width + x].__str__() + ", "
			print(output)

	# Convert's a board position to a visual position, used for graphics
	def board_to_visual_pos(self, pos : int) -> tuple[int, int]:
		return (
			self.base_offset_x + (pos % self.twidth) * self.chosen_size,
			self.base_offset_y + (self.chosen_size * self.height) - self.chosen_size * (int(pos / self.twidth) + 1)
		)

	# Scales images to be to scale
	def resize_sprites(self, sprites):
		for i in range(0, len(sprites.piece_sprites), 1):
			sprites.piece_sprites[i] = pygame.transform.scale(sprites.piece_sprites[i], (self.chosen_size, self.chosen_size))
		for i in range(0, len(sprites.square_sprites), 1):
			sprites.square_sprites[i] = pygame.transform.scale(sprites.square_sprites[i], (math.ceil(self.chosen_size + 0.1), math.ceil(self.chosen_size + 0.1)))
		sprites.move_sprite = pygame.transform.scale(sprites.move_sprite, (self.chosen_size, self.chosen_size))
		sprites.move_highlight_sprite = pygame.transform.scale(sprites.move_highlight_sprite, (self.chosen_size, self.chosen_size))

	# Class for pieces
	class Piece:
		pos : int=0
		visual_pos : int=tuple[int, int]
		type : int=0
		piece_type : int=0
		color : int=0
		color_index : int=0

		# How many times this piece is attacked 0b0000 (x: 0b1100, y: 0b0011)
		attacked : int

		def __init__(self, pos : int, type : int) -> None:
			self.pos = pos
			self.type = type
			self.piece_type = type & 3
			self.color = type & 12
			self.color_index = (self.color >> 2) - 1
			self.reset_attacked()

			# NOTE: You must set the visual position yourself, if you need it ;)

		def __str__(self) -> str:
			# | enemy pieces nearby (x (00), y (00)) | pos | color | type |
			#
			# example: 0110 0010011 10 01
			return str((self.attacked << 11) + (self.pos << 4) + self.type)

		def get_type(self) -> int:
			return self.type & 3

		def get_attacked_x(self) -> int:
			return self.attacked[1][1]

		def get_attacked_y(self) -> int:
			return self.attacked[0][1]

		def reset_attacked(self) -> None:
			self.attacked = 0

	class sprite_storage:
		def __init__(self, piece_sprites : list, square_sprites : list, move_sprite : pygame.Surface, move_highlight_sprite : pygame.Surface) -> None:
			if not len(piece_sprites) == 4 and not len(square_sprites) == 4:
				assert "[ERROR] There must be exactly 4 piece sprites and 4 square sprites"

			self.piece_sprites = piece_sprites
			self.square_sprites = square_sprites
			self.move_sprite = move_sprite
			self.move_highlight_sprite = move_highlight_sprite

	class move:
		def __init__(self, startPos : int, targetPos : int) -> None:
			self.startPos = startPos
			self.targetPos = targetPos
			self.direction = targetPos - startPos
		
		def set_visual_pos(self, game) -> None:
			self.visual_pos = game.board_to_visual_pos(self.targetPos)

	class piece_type(IntEnum):
		NONE = 0,
		PAWN = 1,
		KING = 2,
		BLACK = 4
		WHITE = 8,

	class game_state(IntEnum):
		RUNNING = 0,
		END = 1

if __name__ == '__main__':
	# Read board data from file
	data_file = open(".\\Input.txt", "r")
	data = data_file.read().split("--")[1].replace("\n", "").split(" | ")
	data_file.close()
	size = data[0].split(" ")

	assert len(data) == 2 and len(size) == 2, '[ERROR] There must be exactly 3 parameters\n\nUsage:\n\tpython .\\main.py width height "fen"'

	# Settings
	width = int(size[0])
	height = int(size[1])
	fen = data[1]

	import os
	folder_name = os.getcwd() + "\\Sprites"
	
	app = Hnefetafl(True, Hnefetafl.sprite_storage(
		[
			pygame.image.load(folder_name + "\\Sprite_Black_Piece.png"),
			pygame.image.load(folder_name + "\\Sprite_Black_King.png"),
			pygame.image.load(folder_name + "\\Sprite_White_Piece.png"),
			pygame.image.load(folder_name + "\\Sprite_White_King.png")
		],
		[
			pygame.image.load(folder_name + "\\Sprite_White_Square.png"),
			pygame.image.load(folder_name + "\\Sprite_Black_Square.png"),
			pygame.image.load(folder_name + "\\Sprite_Edge_Square.png"),
			pygame.image.load(folder_name + "\\Sprite_Throne_Square.png")
		],
		pygame.image.load(folder_name + "\\Sprite_Move.png"),
		pygame.image.load(folder_name + "\\Sprite_Move_Highlight.png")
	), fen, width, height)