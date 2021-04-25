import math
import socket
import sys
from time import sleep
import pygame
import pickle

host = '127.0.0.1'
port = 65432

DIMENSION = 8
SQ_SIZE = 64
WIDTH = HEIGHT = 512
MAX_FPS = 30
LIGHT = 1
DARK = 0
X = 0
Y = 1


class server:

    def __init__(self, hostname, port_number):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = hostname
        self.port = port_number

    def connect(self):
        print("Connecting!")
        self.sock.connect((self.host, self.port))
        return

    def get_data(self):
        current_data = self.sock.recv(1024).decode('utf-8')

        return current_data

    def get_data_raw(self):
        current_data = self.sock.recv(1024)

        return current_data

    def send_data(self, message):
        #print("\nSending data!")
        self.sock.send((message.encode('utf-8')))
        # print("Finished sending data!\n")
        return

    def send_data_raw(self, message):
        self.sock.send(message)

        return

    def shutdown(self):
        print("\nClosing connection to server!")
        self.sock.close()
        return


class Checker:

    def __init__(self, coords, r, c, isKing, team):
        self.location = coords
        self.king = isKing
        self.team = team
        self.row = r
        self.column = c
        self.selected = False

    def is_selected(self):
        self.selected = True

    def deselect(self):
        self.selected = False


def draw_board(screen):
    colors = [pygame.Color('white'), pygame.Color('gray')]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)]
            pygame.draw.rect(screen, color, pygame.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
    # pygame.display.update(screen)


def check_for_win(pieces):
    light_pieces_remaining = len(pieces[1])
    dark_pieces_remaining = len(pieces[0])

    # IF white or black has no pieces, return that the other team won the game
    if dark_pieces_remaining == 0:
        print('White Won the Game!')
        return "white"
        # shutdown_game(game_client)
    elif light_pieces_remaining == 0:
        print('Black Won the Game!')
        return "black"
        # shutdown_game(game_client)
    # Otherwise just go back to normal
    else:
        # game_client.send_data('Game is not over')
        return False


def start_game(screen):
    light = pygame.Color('khaki')
    dark = pygame.Color('black')

    light_pieces = []
    dark_pieces = []

    # Now draw the pieces
    for r in range(DIMENSION+1):
        for c in range(DIMENSION+1):
            if c < 4:
                color = dark
            else:
                color = light
            if c == 4 or c == 5:
                continue
            if ((r + c) % 2) != 0 and (c != 4 or 5):
                if color == light and r > 0 and 5 < c < 9:
                    light_pieces.append(Checker([r*SQ_SIZE - (SQ_SIZE / 2), c*SQ_SIZE - (SQ_SIZE / 2)], r, c, 0, 1))
                elif color == dark and r > 0 and 0 < c < 4:
                    dark_pieces.append(Checker([r*SQ_SIZE - (SQ_SIZE / 2), c*SQ_SIZE - (SQ_SIZE / 2)], r, c, 0, 0))
                pygame.draw.circle(screen, color, (r*SQ_SIZE - (SQ_SIZE / 2), c*SQ_SIZE - (SQ_SIZE / 2)), (SQ_SIZE / 2 - 1))

    return [dark_pieces, light_pieces]


def check_for_jumps(piece_to_move, pieces, potential_move):

    new_potential_move = [0, 0]

    # print("Potential Moves to Jump: ", potential_move)
    new_potential_move[0] = 2 * potential_move[0]
    new_potential_move[1] = 2 * potential_move[1]

    return new_potential_move


def check_potential_move(pieces, piece_to_move, potential_move, potential_moves, potential_move_in_cords):
    # print((piece_to_move[1] + potential_move[0]), (piece_to_move[2] + potential_move[1]))
    for each_teams_pieces in pieces:
        for each_piece in each_teams_pieces:
            if (each_piece.row == piece_to_move.row + potential_move[0] and each_piece.column == piece_to_move.column + potential_move[1]):
                # There is another piece on this square.
                if (each_piece.team != piece_to_move.team):  # If the piece is of opposite color/team
                    # Check if a jump can be made
                    new_move = check_for_jumps(piece_to_move, pieces, potential_move)
                    potential_moves.remove(potential_move_in_cords)
                    new_move_in_cords = [(piece_to_move.location[0] + new_move[0] * SQ_SIZE),
                                         (piece_to_move.location[1] + new_move[1] * SQ_SIZE)]
                    potential_moves.append(new_move_in_cords)
                else:
                    # Can't move here, occupied by our own piece, not a viable potential move
                    # print("Cant move here\n\n")
                    potential_moves.remove(potential_move_in_cords)

    return potential_moves


def move_piece(piece, potential_moves, mouse_pos, pieces):

    print(mouse_pos)
    the_move = [piece.row, piece.column]
    print("The Move Default: ", the_move)

    piece_to_remove = None

    # First, determine which move was selected
    for each_move in potential_moves:
        if abs(each_move[0] - mouse_pos[0]) < 32 and abs(each_move[1] - mouse_pos[1]) < 32:
            the_move = each_move

    # Now convert the move to r and c

    print("Current R-C: ", piece.row, piece.column)

    # If move was invalid
    if the_move == [piece.row, piece.column]:
        print("No move made")
        piece.deselect()
        return None
    else:
        the_move = [(the_move[0] + SQ_SIZE / 2) / 64, (the_move[1] + SQ_SIZE / 2) / 64]

    print("The Move: ", the_move)
    # If the move is a jump, its r and c change will be greater than 1. Simply remove the checker in between
    if (abs(the_move[0] - piece.row) > 1):
        print("We chose to jump")
        r_in_between = piece.row - the_move[0]
        c_in_between = piece.column - the_move[1]
        for each_teams_pieces in pieces:
            for each_piece in each_teams_pieces:
                # If a same team piece is on the square that would be the new location of the piece to move upon jump, do not allow jump
                if (piece.row - each_piece.row) == (r_in_between) and (piece.column - each_piece.column) == (c_in_between):

                    print("Invalid jump, another piece already occupies that square")
                    piece.deselect()
                    return None
                elif (piece.row - each_piece.row) == (r_in_between / 2) and (piece.column - each_piece.column) == (c_in_between / 2):
                    print("Removing", the_move)
                    piece_to_remove = each_piece
                else:
                    continue

        print(r_in_between, c_in_between)
    for each_teams_pieces in pieces:
        if piece_to_remove in each_teams_pieces:
            each_teams_pieces.remove(piece_to_remove)




    # Set new moves location to checker
    print(the_move[0] - piece.row, the_move[1] - piece.column)
    piece.location[X] += (the_move[0] - piece.row) * SQ_SIZE
    piece.location[Y] += (the_move[1] - piece.column) * SQ_SIZE

    # Check for king made




    # Set the checkers row and column as well
    piece.row = the_move[0]
    piece.column = the_move[1]

    print('New piece cords: ', piece.location, piece.row, piece.column)

    if (piece.team == LIGHT and piece.column == 1 and piece.king == False):
        print('King!')
        piece.king = True
    if (piece.team == DARK and piece.column == 8 and piece.king == False):
        print('King!')
        piece.king = True
    # Then deselect the checker
    piece.deselect()

    print(potential_moves)
    # Then update the board

    return piece


def get_potential_moves(piece_to_move, pieces):
    # Later we will need code to check if king
    # For now, lets see if we can get the squares diagnally in front
    # Now lets get the team
    if piece_to_move.team == LIGHT:
        team = 'light'
    else:
        team = 'dark'


    potential_moves = []

    if team == 'light' or piece_to_move.king == True:
        # print("Light piece detected")
        r_piece = piece_to_move.row
        c_piece = piece_to_move.column

        # Move up to left diagonal


        # print("Piece cords: ", piece_to_move[0])

        potential_move_1 = [-1, -1]
        potential_moves_1 = [(piece_to_move.location[X] + potential_move_1[0] * SQ_SIZE),
                             (piece_to_move.location[Y] + potential_move_1[1] * SQ_SIZE)]

        potential_moves.append(potential_moves_1)

        # Check if there is a piece on one of the potential squares
        potential_moves = check_potential_move(pieces, piece_to_move, potential_move_1, potential_moves, potential_moves_1)

        # Move up to right diagonal
        potential_move_2 = [1, -1]
        potential_moves_2 = [piece_to_move.location[X] + potential_move_2[0] * SQ_SIZE,
                             piece_to_move.location[Y] + potential_move_2[1] * SQ_SIZE]
        potential_moves.append(potential_moves_2)

        potential_moves = check_potential_move(pieces, piece_to_move, potential_move_2, potential_moves, potential_moves_2)

        # If king


        for each_move in potential_moves:
            if each_move[0] < 0 or each_move[0] > HEIGHT or each_move[1] < 0 or each_move[1] > HEIGHT:
                print("Removing move: ", each_move)
                potential_moves.remove(each_move)

        # Show each good move, and convert back to r and c form

    if team == "dark" or piece_to_move.king == True:
        # print("Light piece detected")
        r_piece = piece_to_move.row
        c_piece = piece_to_move.column

        # Move up to left diagonal

        # print("Piece cords: ", piece_to_move[0])

        potential_move_1 = [-1, 1]
        potential_moves_1 = [(piece_to_move.location[X] + potential_move_1[0] * SQ_SIZE),
                             (piece_to_move.location[Y] + potential_move_1[1] * SQ_SIZE)]
        potential_moves.append(potential_moves_1)


        potential_moves = check_potential_move(pieces, piece_to_move, potential_move_1, potential_moves, potential_moves_1)

        # Move up to right diagonal
        potential_move_2 = [1, 1]
        potential_moves_2 = [piece_to_move.location[X] + potential_move_2[0] * SQ_SIZE,
                             piece_to_move.location[Y] + potential_move_2[1] * SQ_SIZE]
        potential_moves.append(potential_moves_2)


        potential_moves = check_potential_move(pieces, piece_to_move, potential_move_2, potential_moves, potential_moves_2)

        for each_move in potential_moves:
            if each_move[0] < 0 or each_move[0] > HEIGHT or each_move[1] < 0 or each_move[1] > HEIGHT:
                print("Removing move: ", each_move)
                potential_moves.remove(each_move)

        # Show each good move, and convert back to r and c form

    print("Current Position: ", piece_to_move.location, piece_to_move.row, piece_to_move.column)
    print("Available Moves: ", potential_moves)
    return potential_moves


def draw_pieces(screen, pieces):
    light = pygame.Color('khaki')
    dark = pygame.Color('black')

    selected_light = pygame.Color('blue')
    selected_dark = pygame.Color('red')

    king_light = pygame.Color('green')
    king_dark = pygame.Color('yellow')

    light_pieces = []
    dark_pieces = []

    # Now draw the pieces
    for each_team in pieces:
        for each_piece in each_team:
            # print(each_piece)
            if each_piece.team == LIGHT:
                if each_piece.selected == True:
                    color = selected_light
                else:
                    if each_piece.king == True:
                        color = king_light

                    else:
                        color = light

            else:
                if each_piece.selected == True:
                    color = selected_dark
                else:
                    if each_piece.king == True:
                        color = king_dark
                    else:
                        color = dark

            pygame.draw.circle(screen, color, each_piece.location, (SQ_SIZE / 2 - 1))


def get_piece(mouse_pos, pieces, team):
    # print('Yo')
    # print("Clicked here: ", mouse_pos)
    for each_teams_pieces in pieces:
        # Each_teams_pieces represents the individual lists containing Dark pieces and Light pieces
        for each_piece in range(len(each_teams_pieces)):
            # For each piece in the light and dark piece lists
            # Check if the distance the click was registered is on a piece,
            # and ensure that piece is of the color to move (Ie if a black piece is selected, it must be blacks turn)
            if get_distance(each_teams_pieces[each_piece].location, mouse_pos) and each_teams_pieces[each_piece].team == team:
                print(each_teams_pieces[each_piece].team)
                each_teams_pieces[each_piece].is_selected()
                return (each_teams_pieces[each_piece], each_piece, each_teams_pieces[each_piece].team)


    print("No piece found")
    return None


def get_distance(piece_pos, mouse_pos):
    radius = (SQ_SIZE / 2)
    # print(piece_pos, mouse_pos)
    # pygame.draw.rect(screen, pygame.Color('black'), (piece_pos[0], piece_pos[1], SQ_SIZE, SQ_SIZE))
    x_part = (piece_pos[0] - mouse_pos[0])**2
    y_part = (piece_pos[1] - mouse_pos[1])**2
    lhs = math.sqrt(x_part + y_part)
    rhs = math.sqrt(radius ** 2)
    # print(f'Check Distance: {lhs} <= {rhs}')
    if lhs <= rhs:
        # print("Piece found!", piece_pos)
        return True
    else:
        return False


def get_pieces_from_opponent(host_server):
    print('yo')

    # Get the amount of pieces from opponent
    piece_count = host_server.get_data()
    piece_count = int(piece_count)

    raw_pieces = []

    print(piece_count)

    # piece_count = 1

    pieces = [[], []]

    for amount_of_pieces in range(piece_count):
        data = host_server.get_data_raw()
        current_piece = pickle.loads(data)

        # print(type(data[0]), type(data[1]), type(data[2]), type(data[3]))

        raw_pieces.append(current_piece)

    for each in raw_pieces:
        if each.team == LIGHT:
            pieces[LIGHT].append(each)
        else:
            pieces[DARK].append(each)

    return pieces


def send_pieces_to_opponent(host_server, pieces):
    # print("Sending opponent pieces")

    # First tell our client how many pieces are going to be sent
    piece_count = len(pieces[DARK]) + len(pieces[LIGHT])
    print(piece_count)
    host_server.send_data(str(piece_count))

    sleep(0.002)
    # one_piece = pieces[0][1]
    # game_client.send_data(str(one_piece))



    for each_team in pieces:
        for each_piece in each_team:
            current_piece = pickle.dumps(each_piece)
            # print(each_piece)
            host_server.send_data_raw(current_piece)
            sleep(0.0001)


def get_gamestate_from_opponent(host_server):
    data = host_server.get_data()

    return data


def send_gamestate_to_opponent(host_server, gamestate):
    # If no one has won
    if gamestate == False:
        host_server.send_data("No winner")

    elif gamestate == "white":
        host_server.send_data("White won!")

    else:
        host_server.send_data("Black won!")

    return


def main():

    host_server = server(host, port)
    host_server.connect()

    data = host_server.get_data()
    print(data)
    data = host_server.get_data()
    print(data)
    '''
    color_choice = input("Select your color: ")
    host_server.send_data(color_choice)
    data = host_server.get_data()
    print(data)
    color_choice = input("Say yes to play as Black: ")
    host_server.send_data(color_choice)
    data = host_server.get_data()
    print(data)
    '''



    pygame.init()
    pygame.display.set_caption('client')
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    screen.fill(pygame.Color('white'))

    turn = "opponent"

    piece = None
    potential_moves = []

    running = True
    team = 0



    pieces = start_game(screen)
    print(len(pieces), len(pieces[0]), len(pieces[1]))
    piece_team = 0
    piece_index = 0

    draw_board(screen)
    draw_pieces(screen, pieces)
    pygame.display.flip()

    while running:
        draw_board(screen)
        draw_pieces(screen, pieces)

        clock.tick(MAX_FPS)
        pygame.display.flip()

        if turn == 'own':

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if piece is not None:
                        mouse_pos = pygame.mouse.get_pos()
                        piece = move_piece(piece, potential_moves, mouse_pos, pieces)

                        if piece is False:
                            piece = None
                            continue
                        pieces[piece_team][piece_index] = piece
                        print("NEXT MOVE\n\n\n\n")
                        piece = None
                        winner = check_for_win(pieces)

                        send_gamestate_to_opponent(host_server, winner)
                        # If somebody won the game
                        if winner is not False:
                            print("Sending win to other side")
                            host_server.shutdown()
                            exit(0)
                        send_pieces_to_opponent(host_server, pieces)

                        turn = 'opponent'

                    else:
                        # print(pieces[1][4])
                        mouse_pos = pygame.mouse.get_pos()
                        if get_piece(mouse_pos, pieces, 0) is None:
                            continue
                        else:
                            piece, piece_index, piece_team = get_piece(mouse_pos, pieces, 0)
                            potential_moves = get_potential_moves(piece, pieces)

        else:
            game_state = get_gamestate_from_opponent(host_server)

            if game_state != "No winner":
                print(game_state)
                # host_server.send_data('Closing Connection')
                host_server.shutdown()
                exit(0)

            pieces = get_pieces_from_opponent(host_server)



            turn = 'own'


if __name__ == '__main__':
    main()

