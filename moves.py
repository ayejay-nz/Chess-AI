from gamestate import WK, WQ, BK, BQ


def is_occupied_index(bitboards, square_index):
    """
    Check if a square is occupied by a piece given a set of bitboards
    """

    square = 2**square_index

    for bb in bitboards:
        if bb & square:
            return True

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


def get_castling_rights(castling_rights):
    """
    Returns a tuple of booleans of the current castling rights

    (black queenside, black kingside, white queenside, white kingside)
    """

    return (
        castling_rights & BQ == BQ,
        castling_rights & BK == BK,
        castling_rights & WQ == WQ,
        castling_rights & WK == WK,
    )


def find_pawn_moves(player_bbs, opposition_bbs, is_whites_move, en_passant_temp_idx):
    """
    Find possible pawn moves
    """

    def can_forward_move(square, rank):
        """
        Check if a pawn can do a regular or double forward move, and returns whichever ones it can do
        """

        moves = []

        # Check if a pawn can move a single square forward
        move_square = square + 8 if is_whites_move else square - 8
        can_single_move = not is_occupied_index(player_bbs + opposition_bbs, move_square)

        if not can_single_move:
            return moves

        moves.append((square, move_square))

        # Check if a pawn can double move forward
        move_square = square + 16 if is_whites_move else square - 16
        # Only allow double moves on home row
        on_home_row = (rank == 1 and is_whites_move) or (rank == 6 and not is_whites_move)

        if not on_home_row:
            return moves

        can_double_move = not is_occupied_index(player_bbs + opposition_bbs, move_square)

        if not can_double_move:
            return moves

        moves.append((square, move_square))
        return moves

    pawn_bb = player_bbs[0]

    pawn_capture_moves = [7, 9] if is_whites_move else [-7, -9]

    moves = []
    capture_moves = []

    while pawn_bb:
        lsb = pawn_bb & -pawn_bb
        square = lsb.bit_length() - 1
        rank = get_rank(square)

        moves.extend(can_forward_move(square, rank))

        for move in pawn_capture_moves:
            move_square = square + move
            move_rank = get_rank(move_square)

            # Check if capture move went around the edge of the board, i.e., it moves zero or two ranks
            if abs(rank - move_rank) != 1:
                continue

            # Check if square has enemy piece which can be captured
            if is_occupied_index(opposition_bbs, move_square):
                capture_moves.append((square, move_square))

            # En passant
            if move_square == en_passant_temp_idx:
                capture_moves.append((square, move_square))

        pawn_bb ^= lsb

    return (capture_moves, moves)


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


def find_knight_moves(player_bbs):
    """
    Find possible knight moves
    """

    knight_bb = player_bbs[2]

    knight_moves = [(2, -1), (2, 1), (1, 2), (1, -2), (-2, 1), (-2, -1), (-1, -2), (-1, 2)]

    moves = []

    while knight_bb:
        lsb = knight_bb & -knight_bb
        square = lsb.bit_length() - 1
        rank = get_rank(square)
        file = get_file(square)

        for dr, df in knight_moves:
            move_rank = rank + dr
            if move_rank > 7 or move_rank < 0:
                continue

            move_file = file + df
            if move_file > 7 or move_file < 0:
                continue

            move_square = 8 * move_rank + move_file

            # Blocked by own piece
            if is_occupied_index(player_bbs, move_square):
                continue

            moves.append((square, move_square))

        knight_bb ^= lsb

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


def find_king_moves(player_bbs, opposition_bbs, is_whites_move, castling_rights):
    """
    Find possible king moves
    """

    moves = []
    castling_moves = []

    king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    king_bb = player_bbs[5]
    if king_bb == 0:
        return moves

    square = king_bb.bit_length() - 1
    rank = get_rank(square)
    file = get_file(square)

    kingside_free, queenside_free = False, False
    for dr, df in king_moves:
        move_rank = rank + dr
        move_file = file + df

        if 0 <= move_rank <= 7 and 0 <= move_file <= 7:
            move_square = 8 * move_rank + move_file

            # Blocked by friendly piece
            if is_occupied_index(player_bbs, move_square):
                continue

            moves.append((square, move_square))

            # If a left/right move is a capturing move, i.e. you cannot castle in that direction
            if dr != 0 or is_occupied_index(opposition_bbs, move_square):
                continue

            # Square to the left (kingside) or right (queenside) of king is free
            if df == 1:
                kingside_free = True
            else:
                queenside_free = True
        else:
            continue

    BQ_rights, BK_rights, WQ_rights, WK_rights = get_castling_rights(castling_rights)

    k_step, q_step = 2, -2
    q_extra = -1
    k_rook_step, q_rook_step = 3, -4
    if is_whites_move:
        k_rights, q_rights = WK_rights, WQ_rights
    else:
        k_rights, q_rights = BK_rights, BQ_rights

    # check kingside castling
    if kingside_free and k_rights:
        # check rook exists
        rook_square = square + k_rook_step
        rook_exists = is_occupied_index([player_bbs[1]], rook_square)

        move_square = square + k_step
        if not is_occupied_index(player_bbs + opposition_bbs, move_square) and rook_exists:
            castling_moves.append((square, move_square))

    # check queenside castling
    if queenside_free and q_rights:
        # check rook exists
        rook_square = square + q_rook_step
        rook_exists = is_occupied_index([player_bbs[1]], rook_square)

        move_square = square + q_step
        if (
            not is_occupied_index(player_bbs + opposition_bbs, move_square)
            and not is_occupied_index(player_bbs + opposition_bbs, move_square + q_extra)
            and rook_exists
        ):
            castling_moves.append((square, move_square))

    return moves, castling_moves


def in_check(king_square, opposition_moves):
    """
    Check if the opponents pieces can attack the king
    """

    return any(sq == king_square for _, sq in opposition_moves)


def filter_legal_moves(
    pseudo_legal_moves,
    player_bbs,
    opposition_bbs,
    is_whites_move,
    castling_rights,
    en_passant_temp_idx,
    en_passant_real_idx,
):
    """
    Convert a list of all pseudo-legal moves into legal moves, i.e. remove all moves that result in a check
    """

    legal_moves = []

    def filter_moves(moves):
        """
        Find all moves from a set of moves which result in the king not being in check
        """

        for move in moves:
            new_player_bbs, new_opposition_bbs, new_en_passant_temp_idx, _ = apply_move(
                player_bbs, opposition_bbs, move, en_passant_temp_idx, en_passant_real_idx
            )

            # See if an opponents piece can attack the king
            king_bb = new_player_bbs[5]
            king_square = king_bb.bit_length() - 1

            o_piece_capturing_moves, o_king_moves, _, _ = find_pseudo_legal_moves(
                new_opposition_bbs,
                new_player_bbs,
                not is_whites_move,
                castling_rights,
                new_en_passant_temp_idx,
            )

            # Move results in check
            if not in_check(king_square, o_piece_capturing_moves + o_king_moves):
                legal_moves.append(move)

    piece_moves, king_moves, castling_moves, pawn_moves = pseudo_legal_moves

    # Find safe king moves
    filter_moves(king_moves)

    # See if the king would be castling through check
    kingside_clear = True if (4, 5) in legal_moves or (60, 61) in legal_moves else False
    queenside_clear = True if (4, 3) in legal_moves or (60, 59) in legal_moves else False

    # Find piece moves leaving king safe
    filter_moves(piece_moves + pawn_moves)

    if len(castling_moves) == 0:
        return legal_moves

    # Cannot castle out of check
    king_bb = player_bbs[5]
    king_square = king_bb.bit_length() - 1
    o_piece_capturing_moves, o_king_moves, _, _ = find_pseudo_legal_moves(
        opposition_bbs, player_bbs, not is_whites_move, castling_rights, en_passant_temp_idx
    )

    if in_check(king_square, o_piece_capturing_moves):
        return legal_moves

    for move in castling_moves:
        start_square = move[0]
        end_square = move[1]
        move_delta = end_square - start_square

        # King doesn't pass through check and doesn't land in check
        if (
            move_delta == 2
            and kingside_clear
            and not in_check(end_square, o_piece_capturing_moves + o_king_moves)
        ):
            legal_moves.append(move)
        elif (
            move_delta == -2
            and queenside_clear
            and not in_check(end_square, o_piece_capturing_moves + o_king_moves)
        ):
            legal_moves.append(move)

    return legal_moves


def apply_move(player_bbs, opposition_bbs, move, en_passant_temp_idx, en_passant_real_idx):
    """
    Apply a users move to their bitboard, and return the modified bitboards
    """

    start_idx, end_idx = move
    move_delta = end_idx - start_idx
    start_square, end_square = 2**start_idx, 2**end_idx

    new_player = player_bbs[:]
    new_opposition = opposition_bbs[:]

    new_en_passant_temp_idx = 0
    new_en_passant_real_idx = 0

    for idx, bb in enumerate(new_player):
        # Find the bitboard containing the piece which is moved
        if bb & start_square:
            # Castling moves both the king and a rook
            if idx == 5 and move_delta in (2, -2):
                if move_delta == 2:  # Kingside
                    rook_idx = start_idx + 3
                    rook_end_idx = rook_idx - 2
                else:  # Queenside
                    rook_idx = start_idx - 4
                    rook_end_idx = rook_idx + 3

                rook_end_square = 2**rook_end_idx
                rook_square = 2**rook_idx

                new_player[1] = new_player[1] ^ rook_square  # Remove the castled rook
                new_player[1] = new_player[1] ^ rook_end_square  # Place the castled rook

            # Update temp pawn data on a pawn double move for en passant
            if idx == 0 and move_delta in (16, -16):
                new_en_passant_temp_idx = start_idx + move_delta // 2
                new_en_passant_real_idx = end_idx  # pawn that is captured

            new_player[idx] = new_player[idx] ^ start_square  # Remove the moved piece
            new_player[idx] = new_player[idx] ^ end_square  # Place the moved piece
            break

    for idx, bb in enumerate(new_opposition):
        # Remove captured piece
        if bb & end_square:
            new_opposition[idx] = new_opposition[idx] ^ end_square
            break

        # Remove en passanted pawn
        if idx == 0 and end_square == 2**en_passant_temp_idx:
            new_opposition[0] = new_opposition[0] ^ 2**en_passant_real_idx

    return new_player, new_opposition, new_en_passant_temp_idx, new_en_passant_real_idx


def find_pseudo_legal_moves(
    player_bbs, opposition_bbs, is_whites_move, castling_rights, en_passant_temp_idx
):
    """
    Find all pseudo-legal moves for the given player

    Returns a list of all capturing moves, castling moves, and forward pawn moves
    """

    # Store pseudo-legal moves for each piece type as (start square, end square)
    pawn_capturing_moves, pawn_moves = find_pawn_moves(
        player_bbs, opposition_bbs, is_whites_move, en_passant_temp_idx
    )
    king_moves, castling_moves = find_king_moves(
        player_bbs, opposition_bbs, is_whites_move, castling_rights
    )
    piece_capturing_moves = (
        pawn_capturing_moves
        + find_rook_moves(player_bbs, opposition_bbs)
        + find_knight_moves(player_bbs)
        + find_bishop_moves(player_bbs, opposition_bbs)
        + find_queen_moves(player_bbs, opposition_bbs)
    )

    return piece_capturing_moves, king_moves, castling_moves, pawn_moves


def find_legal_moves(
    white_bbs, black_bbs, is_whites_move, castling_rights, en_passant_temp_idx, en_passant_real_idx
):
    """
    Find all legal moves for the given player

    Returns a list of all capturing moves and a list of non-capturing moves (i.e. forward pawn moves)
    """

    player_bbs = white_bbs if is_whites_move else black_bbs
    opposition_bbs = black_bbs if is_whites_move else white_bbs

    pseudo_legal_moves = find_pseudo_legal_moves(
        player_bbs, opposition_bbs, is_whites_move, castling_rights, en_passant_temp_idx
    )

    legal_moves = filter_legal_moves(
        pseudo_legal_moves,
        player_bbs,
        opposition_bbs,
        is_whites_move,
        castling_rights,
        en_passant_temp_idx,
        en_passant_real_idx,
    )

    return legal_moves
