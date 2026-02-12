import gamestate
from helpers import set_gamestate, reset_gamestate, game_bbs_from_indexes


def test_set_gamestate():
    set_gamestate(False, False, 0, 40, 48, 50, {"x": 2})

    assert gamestate.is_whites_move is False
    assert gamestate.is_playing_white is False
    assert gamestate.castling_rights == 0
    assert gamestate.temp_pawn_idx == 40
    assert gamestate.real_pawn_idx == 48
    assert gamestate.halfmove_clock == 50
    assert gamestate.position_counts == {"x": 2}


def test_reset_gamestate():
    reset_gamestate()

    assert gamestate.is_whites_move is True
    assert gamestate.is_playing_white is True
    assert gamestate.castling_rights == 15
    assert gamestate.temp_pawn_idx == 0
    assert gamestate.real_pawn_idx == 0
    assert gamestate.halfmove_clock == 0
    assert gamestate.position_counts == {}


def test_game_bbs_from_indexes():
    pawn_idxs = ([8, 9, 10, 11, 12, 13, 14, 15], [48, 49, 50, 51, 52, 53, 54, 55])
    rook_idxs = ([0, 7], [56, 63])
    knight_idxs = ([1, 6], [57, 62])
    bishop_idxs = ([2, 5], [58, 61])
    queen_idxs = ([3], [59])
    king_idxs = ([4], [60])
    bbs = game_bbs_from_indexes(
        pawn_idxs, rook_idxs, knight_idxs, bishop_idxs, queen_idxs, king_idxs
    )

    expected_white_bb_values = [65280, 129, 66, 36, 8, 16]
    expected_black_bb_values = [
        71776119061217280,
        9295429630892703744,
        4755801206503243776,
        2594073385365405696,
        576460752303423488,
        1152921504606846976,
    ]

    assert len(bbs) == 2
    assert len(bbs[0]) == len(bbs[1]) == 6
    for idx, bb in enumerate(bbs[0]):
        assert bb == expected_white_bb_values[idx]
    for idx, bb in enumerate(bbs[1]):
        assert bb == expected_black_bb_values[idx]
