PLAYER_ON_BOTTOM = True

is_whites_move = True
is_playing_white = True

WK, WQ, BK, BQ = 1, 2, 4, 8
castling_rights = WK | WQ | BK | BQ
ROOK_START_RIGHTS = {
    (True, 0): WQ,
    (True, 7): WK,
    (False, 56): BQ,
    (False, 63): BK,
}

temp_pawn_idx = 0
real_pawn_idx = 0

halfmove_clock = 0
