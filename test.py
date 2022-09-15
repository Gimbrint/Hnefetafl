from enum import IntEnum
import pygame
import math

class Hnefetafl:
	def __init__(self, whiteToMove : bool) -> None:
		self.directions : list = [8, 1, -8, -1]
		self.hexDirections : list = [16, -16, 1, -1]

		self.board : list = [None for x in range(64)]
		self.attackBoard : list = [list() for x in range(64)]
		
		self.pieces : list = [list() for x in range(2)]

		self.whiteToMove = whiteToMove
		self.friendlyColorIndex = int(whiteToMove)
		self.opponentColorIndex = 1 - self.friendlyColorIndex

		# | enemy pieces nearby (x (00), y (00)) | pos | color | type |
		#			0101 000000 00 00
		#			1000 001001 01 10
		#			1000 000000 11 11
		#			0100 000000 11 11
		#			0000 000000 00 00
		self.typeMask = 15
		self.pieceTypeMask = 3
		self.colorMask = 3 << 2
		self.posMask = 63 << 4
		self.attackXMask = 3 << 12
		self.attackYMask = 3 << 10

		# Window
		self.screenX = 1024
		self.screenY = 400
		self.screen = pygame.display.set_mode((self.screenX, self.screenY))
		
		# Used for square generating
		self.chosen_size = min(self.screenX, self.screenY) / 8
		self.base_offset_x = max(self.screenX - self.screenY, 0) / 2
		self.base_offset_y = max(self.screenY - self.screenX, 0) / 2

		even_color = (255, 0, 0)
		odd_color = (0, 255, 0)

		# Test stuff
		self.add_piece(2, self.piece_type.KING | self.piece_type.WHITE)
		self.add_piece(0, self.piece_type.KING | self.piece_type.WHITE)
		self.add_piece(16, self.piece_type.KING | self.piece_type.BLACK)
		self.add_piece(9, self.piece_type.KING | self.piece_type.BLACK)
		#self.calculate_attack_squares()
		#self.make_move(self.move(0, 8))
		#self.make_move(self.move(2, 10))
		self.log_board(self.board, 8, 8)

		pygame.init()

		# Closing loop
		selected_piece = -1
		start_pos = 0
		held_down = False
		running = True

		while running:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
					pygame.quit()
				if event.type == pygame.MOUSEBUTTONDOWN: # Select piece
					mousePos = pygame.mouse.get_pos()

					if self.is_mouse_inside_board(mousePos):
						selected_pos = self.get_mouse_to_board_pos(mousePos)

						print(selected_pos)
						if self.board[selected_pos] != 0:
							held_down = True
							selected_piece = selected_pos
							start_pos = self.board[selected_piece].visual_pos
							print("Start")
				if event.type == pygame.MOUSEBUTTONUP: # Drop piece
					if (selected_piece != -1):
						held_down = False

						self.board[selected_piece].visual_pos = start_pos
						selected_piece = -1
						print("YES!!!")
				if held_down and selected_piece != -1: # Drag piece
					self.board[selected_piece].visual_pos = pygame.mouse.get_pos()
					pass

			# Background color
			background_color = (255, 255, 255)
			self.screen.fill(background_color)

			# Generate squares
			for x in range(8):
				for y in range(8):
					rect = pygame.rect.Rect(self.base_offset_x + self.chosen_size * x, self.base_offset_y + self.chosen_size * y, self.chosen_size, self.chosen_size)
					color = even_color
					if (x + y) & 1:
						color = odd_color

					pygame.draw.rect(self.screen, color, rect)

			# Generate pieces
			for i in range(len(self.pieces)):
				for j in range(len(self.pieces[i])):
					piece = self.board[self.pieces[i][j]]
					colorType = piece.color

					color = (30, 30, 30)
					if colorType == self.piece_type.WHITE:
						color = (200, 200, 200)

					pygame.draw.circle(self.screen, color, self.board[self.pieces[i][j]].visual_pos, self.chosen_size / 2)

			pygame.display.flip()

	# Class for pieces
	class Piece:
		pos : int=0
		visual_pos : int=tuple[int, int]
		type : int=0
		color : int=0
		color_index : int=0
		attacked : int=0

		def __init__(self, pos : int, type : int) -> None:
			self.pos = pos
			self.type = type
			self.color = type & 12
			self.color_index = self.color >> 2

			# NOTE: You must set the visual position yourself, if you need it ;)

		def __str__(self) -> str:
			# | enemy pieces nearby (x (00), y (00)) | pos | color | type |
			#
			# example: 0110 010011 10 01
			return str((self.attacked << 10) + (self.pos << 4) + self.type)

		def get_type(self) -> int:
			return self.type & 3

		def get_attacked_x(self) -> int:
			return (self.attacked >> 2) & 3

		def get_attacked_y(self) -> int:
			return self.attacked & 3

		# Set's the visual position, used for graphics
		def set_visual_pos(self, game, pos : int) -> None:
			self.visual_pos = (
				game.base_offset_x + (pos & 7) * game.chosen_size + game.chosen_size / 2,
				game.base_offset_y + (game.chosen_size * 8) -  (pos >> 3) * game.chosen_size - game.chosen_size / 2
			)

	def gen_moves(self, pos : int, isLong : bool=False) -> list:
		piece = self.board[pos]

		# Default movement (1 tile long move)
		#	0 0 0 0 0
		#	0 0 X 0 0
		#	0 X P X 0
		#	0 0 X 0 0
		#	0 0 0 0 0
		if not isLong:
			for i in range(0, self.directions, 1):
				direction = self.directions[i]
		# Long movement (infinite tile long move)
		#	0 0 X 0 0
		#	0 0 X 0 0
		#	X X P X X
		#	0 0 X 0 0
		#	0 0 X 0 0
		else:
			pass

	def add_piece(self, pos : int, type : int) -> None:
		self.board[pos] = self.Piece(pos=pos, type=type)
		self.board[pos].set_visual_pos(self, pos)
		self.pieces[((type & self.colorMask) >> 2) - 1].append(pos)

	def capture_piece(self, pos : int) -> None:
		self.pieces[self.board[pos].color_index].remove(pos)
		self.board[pos] = None

	# Makes a move on the board
	def make_move(self, move) -> None:
		if self.board[move.startPos] != None and self.board[move.targetPos] == None and self.is_inside_board(self.convert_to_hex_board(move.targetPos)):
			piece : self.Piece = self.board[move.startPos]

			# Remove old pos
			self.board[move.startPos] = None
			self.pieces[piece.colorIndex].remove(move.startPos)
			self.piece_pos[move.startPos] = 0

			# Add new pos
			piece.set_visual_pos(self, move.targetPos)
			self.board[move.targetPos] = piece
			self.pieces[piece.colorIndex].append(move.targetPos)

			# Check if there are enemy pieces on the target pos, if so, we attack them and they attact us
			if len(self.attackBoard[move.targetPos]) > 0:
				for i in range(0, len(self.attackBoard[move.targetPos]), 1):
					pos = self.attackBoard[move.targetPos][i]
					mask = 1 << ((pos & 1) * 2)
					
					self.board[pos >> 1].attacks += mask
					self.board[move.targetPos].attacks += mask

					# TODO: Finish this
					if (self.board[pos >> 1].attacks & 3) >= 2 or ((self.board[pos >> 1].attacks >> 2) & 3) >= 2: # X and Y
						print("Killed")
						self.capture_piece(pos >> 1)

			self.calculate_attack_squares()

	def calculate_attack_squares(self) -> None:
		self.attackBoard = [list() for x in range(64)]
		opponentPieces : list = self.pieces[self.opponentColorIndex]

		for i in range(0, len(opponentPieces), 1):
			for j in range(0, len(self.hexDirections), 1):
				# Yeah, i don't know how i came up with this
				targetHex = self.convert_to_hex_board(opponentPieces[i]) + self.hexDirections[j]

				if self.is_inside_board(targetHex):
					# NOTE: Add piece pos on the square (contains all pieces that are around the square)
					isX : int = j > 1
					self.attackBoard[targetHex - (abs(targetHex) >> 4) * 8].append((opponentPieces[i] << 1) | isX)

	def convert_to_hex_board(self, pos : int) -> int:
		return pos + (pos >> 3) * 8

	def is_inside_board(self, pos : int) -> bool:
		if pos & 0x88:
			return False
		return True

	def is_mouse_inside_board(self, pos : tuple[int, int]) -> bool:
		board_pos_x = pos[0] - self.base_offset_x
		board_pos_y = pos[1] - self.base_offset_y

		if board_pos_x < 0 or board_pos_y < 0 or board_pos_x > self.chosen_size * 8 or board_pos_y > self.chosen_size * 8:
			return False
		return True

	def get_mouse_to_board_pos(self, pos : tuple[int, int]) -> int:
		x = math.floor((pos[0] - self.base_offset_x) / self.chosen_size)
		y = math.floor((self.screenY - self.base_offset_y - pos[1] - self.base_offset_y) / self.chosen_size)
		return y * 8 + x

	def log_board(self, board : list, width : int, height : int) -> None:
		for y in range(height - 1, -1, -1):
			output = ""

			for x in range(0, width, 1):
				output += str(y * width + x) + " | " + board[y * width + x].__str__() + ", "

			print(output)

	class move:
		def __init__(self, startPos : int, targetPos : int) -> None:
			self.startPos = startPos
			self.targetPos = targetPos
			self.direction = targetPos - startPos

	class piece_type(IntEnum):
		NONE = 0,
		PAWN = 1,
		KING = 2,
		BLACK = 4
		WHITE = 8,

if __name__ == '__main__':
	# | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
	# | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
	# | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
	# | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
	# | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
	# | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
	# | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
	# | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
	app = Hnefetafl(True)
	app.board[4] = 2
