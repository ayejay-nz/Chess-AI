from pathlib import Path

from zobrist import compute_polyglot_key

ENTRY_SIZE = 16
BOOK_PATH = Path(__file__).resolve().parent / "../../../books" / "Cerebellum3Merge.bin"

promotion_map = {
    0: None,
    1: "n",
    2: "b",
    3: "r",
    4: "q",
}


def probe_opening_book(white_bbs, black_bbs, castling_rights, en_passant_temp_idx, is_whites_move):
    """
    Probe the opening book .bin file and return the best move
    """

    def _decode_entry(entry):
        """
        Convert 16 byte entry into the four segments (key, move, weight, learn)
        """

        return (
            int.from_bytes(entry[0:8], "big"),
            int.from_bytes(entry[8:10], "big"),
            int.from_bytes(entry[10:12], "big"),
            int.from_bytes(entry[12:16], "big"),
        )

    def _book_move_to_engine_move(book_move):
        """
        Convert a book move to engine move format
        """

        to_file = book_move & 0x7
        to_row = (book_move >> 3) & 0x7
        from_file = (book_move >> 6) & 0x7
        from_row = (book_move >> 9) & 0x7
        promo_code = (book_move >> 12) & 0x7

        start_idx = (from_row << 3) | from_file
        end_idx = (to_row << 3) | to_file

        if promo_code not in promotion_map:
            return None

        promotion_piece = promotion_map[promo_code]

        # Convert polyglot castling format -> engine format
        king_bb = white_bbs[5] if is_whites_move else black_bbs[5]
        king_square = king_bb.bit_length() - 1

        if king_square != 4 and king_square != 60:
            return (start_idx, end_idx, promotion_piece)

        if start_idx == 4 and end_idx == 7:  # e1h1
            end_idx = 6  # e1g1
        elif start_idx == 4 and end_idx == 0:  # e1a1
            end_idx = 2  # e1c1
        elif start_idx == 60 and end_idx == 63:  # e8h8
            end_idx = 62  # e8g8
        elif start_idx == 60 and end_idx == 56:  # e8a8
            end_idx = 58  # e8c8

        return (start_idx, end_idx, promotion_piece)

    key = compute_polyglot_key(
        white_bbs, black_bbs, castling_rights, en_passant_temp_idx, is_whites_move
    )

    if not BOOK_PATH.exists():
        return None

    with open(BOOK_PATH, "rb") as b:
        # Get total entries in book
        b.seek(0, 2)
        size = b.tell()
        n_entries = size // ENTRY_SIZE
        if n_entries == 0:
            return None

        # Find first index where entry_key >= key
        lo, hi = 0, n_entries
        while lo < hi:
            mid = (lo + hi) // 2
            b.seek(mid * ENTRY_SIZE)
            entry = b.read(ENTRY_SIZE)
            if len(entry) != ENTRY_SIZE:
                return None

            entry_key, _, _, _ = _decode_entry(entry)
            if entry_key < key:
                lo = mid + 1
            else:
                hi = mid

        # No match
        if lo >= n_entries:
            return None

        # Find all matching openings
        matches = []
        i = lo

        while i < n_entries:
            b.seek(i * ENTRY_SIZE)
            entry = b.read(ENTRY_SIZE)
            if len(entry) != ENTRY_SIZE:
                break

            k, move, weight, _ = _decode_entry(entry)
            if k != key:
                break

            matches.append((move, weight))
            i += 1

        if not matches:
            return None

        # Return strongest book move
        book_move, _ = max(matches, key=lambda x: x[1])

        return _book_move_to_engine_move(book_move)
