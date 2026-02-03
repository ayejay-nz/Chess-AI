def is_occupied_index(bitboards, square_index):
    """
    Check if a square is occupied by a piece given a set of bitboards
    """

    square = 2**square_index

    for bb in bitboards:
        if bb & square: return True

    return False

def get_rank(square):
    """
    Get a squares rank (0-7) from its index
    """

    return square // 8

def get_file(square):
    """
    Get a squares file (0-7) from its index
    """

    return square % 8

def walk_ray(square, player_bbs, opposition_bbs, rank, file, dr, df):
    """
    Walk one direction until blocked or reached edge of the board and return all valid moves
    """

    moves = []

    move_rank, move_file = rank + dr, file + df
    while 0 <= move_rank <= 7 and 0 <= move_file <= 7:
        move_square = 8 * move_rank + move_file

        # Blocked by own piece
        if is_occupied_index(player_bbs, move_square):
            break

        moves.append((square, move_square))

        # Capturing so stop ray
        if is_occupied_index(opposition_bbs, move_square):
            break

        move_rank += dr
        move_file += df

    return moves

def find_pawn_moves(player_bbs, opposition_bbs, bottom_players_move):
    """
    Find possible pawn moves
    """

    def can_forward_move(square, rank):
        """
        Check if a pawn can do a regular or double forward move, and returns whichever ones it can do
        """

        moves = []

        # Check if a pawn can move a single square forward
        move_square = square + 8 if bottom_players_move else square - 8
        can_single_move = not is_occupied_index(player_bbs + opposition_bbs, move_square)

        if not can_single_move:
            return moves

        moves.append((square, move_square))

        # Check if a pawn can double move forward
        move_square = square + 16 if bottom_players_move else square - 16
        # Only allow double moves on home row
        on_home_row = (rank == 1 and bottom_players_move) or (rank == 6 and not bottom_players_move)

        if not on_home_row:
            return moves

        can_double_move = not is_occupied_index(player_bbs + opposition_bbs, move_square)

        if not can_double_move:
            return moves
        
        moves.append((square, move_square))
        return moves

    pawn_bb = player_bbs[0]

    pawn_capture_moves = [7, 9] if bottom_players_move else [-7, -9]

    moves = []

    while pawn_bb:
        lsb = pawn_bb & -pawn_bb
        square = lsb.bit_length() - 1
        rank = get_rank(square)

        moves.extend(can_forward_move(square, rank))

        for move in pawn_capture_moves:
            move_square = square + move
            move_rank = get_rank(move_square)

            # Check if capture move went around the edge of the board, i.e., it jumps two ranks
            if abs(rank - move_rank) > 1:
                continue

            # Check if square has enemy piece which can be captured
            if is_occupied_index(opposition_bbs, move_square): 
                moves.append((square, move_square))

        pawn_bb ^= lsb

    return moves

def find_rook_moves(player_bbs, opposition_bbs):
    """
    Find possible rook moves
    """

    rook_bb = player_bbs[1]

    moves = []

    while rook_bb:
        lsb = rook_bb & -rook_bb
        square = lsb.bit_length() - 1
        rank = get_rank(square)
        file = get_file(square)

        # Check all 4 rook directions: right, left, up, down
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 1, 0))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, -1, 0))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 0, 1))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 0, -1))

        rook_bb ^= lsb

    return moves

def find_bishop_moves(player_bbs, opposition_bbs):
    """
    Find possible bishop moves
    """

    bishop_bb = player_bbs[3]

    moves = []

    while bishop_bb:
        lsb = bishop_bb & -bishop_bb
        square = lsb.bit_length() - 1
        rank = get_rank(square)
        file = get_file(square)

        # Check all 4 bishop directions
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 1, 1))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 1, -1))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, -1, 1))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, -1, -1))

        bishop_bb ^= lsb

    return moves

def find_queen_moves(player_bbs, opposition_bbs):
    """
    Find possible queen moves
    """

    queen_bb = player_bbs[4]

    moves = []

    while queen_bb:
        lsb = queen_bb & -queen_bb
        square = lsb.bit_length() - 1
        rank = get_rank(square)
        file = get_file(square)

        # Check all 8 queen directions
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 1, 0))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, -1, 0))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 0, 1))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 0, -1))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 1, 1))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, 1, -1))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, -1, 1))
        moves.extend(walk_ray(square, player_bbs, opposition_bbs, rank, file, -1, -1))

        queen_bb ^= lsb

    return moves
def find_legal_moves(white_bbs, black_bbs, is_white: bool, is_whites_move: bool):
    """
    Find all legal moves for the given player
    """

    player_bbs = white_bbs if is_whites_move else black_bbs
    opposition_bbs = black_bbs if is_whites_move else white_bbs

    bottom_players_move = not (is_white ^ is_whites_move)

    # Store pseudo-legal moves for each piece type as (start square, end square)
    moves = [
        find_pawn_moves(player_bbs, opposition_bbs, bottom_players_move), 
        find_rook_moves(player_bbs, opposition_bbs), 
        find_bishop_moves(player_bbs, opposition_bbs), 
        find_queen_moves(player_bbs, opposition_bbs), 
    ]

