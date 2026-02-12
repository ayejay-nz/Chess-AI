import gamestate
import moves

from helpers import (
    game_bbs_from_indexes,
    init_default_bbs,
    reset_gamestate,
    set_gamestate,
    pad_move_tuples,
)


class TestFindLegalPawnMoves:
    def test_pawn_forward_moves(self):
        reset_gamestate()
        set_gamestate(castling_rights=0)
        bbs = game_bbs_from_indexes(pawn_idxs=([8, 17], [48, 41]), king_idxs=([4], [60]))
        legal_moves = moves.find_legal_moves(
            bbs[0],
            bbs[1],
            gamestate.is_whites_move,
            gamestate.castling_rights,
            gamestate.temp_pawn_idx,
            gamestate.real_pawn_idx,
            gamestate.halfmove_clock,
        )

        # Expected pawn moves for white
        white_expected_moves = pad_move_tuples([(8, 16), (8, 24), (17, 25)])
        assert set(white_expected_moves).issubset(legal_moves)

        set_gamestate(castling_rights=0, is_whites_move=False)
        legal_moves = moves.find_legal_moves(
            bbs[1],
            bbs[0],
            gamestate.is_whites_move,
            gamestate.castling_rights,
            gamestate.temp_pawn_idx,
            gamestate.real_pawn_idx,
            gamestate.halfmove_clock,
        )

        # Expected pawn moves for black
        black_expected_moves = pad_move_tuples([(48, 40), (48, 32), (41, 33)])
        assert set(black_expected_moves).issubset(legal_moves)

    def test_pawn_capture_moves(self):
        reset_gamestate()
        set_gamestate(castling_rights=0)
        bbs = game_bbs_from_indexes(
            pawn_idxs=([8, 9], [17, 18]), rook_idxs=([], [16]), king_idxs=([0], [56])
        )
        legal_moves = moves.find_legal_moves(
            bbs[0],
            bbs[1],
            gamestate.is_whites_move,
            gamestate.castling_rights,
            gamestate.temp_pawn_idx,
            gamestate.real_pawn_idx,
            gamestate.halfmove_clock,
        )

        # a pawn should not capture as it is pinned
        white_unexpected_move = pad_move_tuples([(8, 17)])[0]
        white_expected_moves = pad_move_tuples([(9, 16), (9, 18)])
        assert set(white_expected_moves).issubset(legal_moves)
        assert white_unexpected_move not in legal_moves

    def test_pawn_en_passant_moves(self):
        reset_gamestate()
        set_gamestate(castling_rights=0, temp_pawn_idx=41, real_pawn_idx=33)
        bbs = game_bbs_from_indexes(
            pawn_idxs=([32, 34], [33]), rook_idxs=([], [58]), king_idxs=([2], [60])
        )
        legal_moves = moves.find_legal_moves(
            bbs[0],
            bbs[1],
            gamestate.is_whites_move,
            gamestate.castling_rights,
            gamestate.temp_pawn_idx,
            gamestate.real_pawn_idx,
            gamestate.halfmove_clock,
        )

        # c file pawn is pinned to king, so only a file pawn can capture
        expected_en_passant = pad_move_tuples([(32, 41)])[0]
        unexpected_en_passant = pad_move_tuples([(34, 41)])[0]

        assert expected_en_passant in legal_moves
        assert unexpected_en_passant not in legal_moves
