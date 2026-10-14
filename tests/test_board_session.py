import json
import pickle
import unittest

from renmodpy import BoardSession
from renmodpy.tactics import Cell, GOAL


class BoardSessionTests(unittest.TestCase):
    def test_completed_route_round_trips_without_renderers(self):
        board = BoardSession()
        state = board.tactics_state()
        path = state.movement_field(state.selected).path_to(GOAL)
        self.assertTrue(path)
        for cell in path[1:]:
            self.assertTrue(board.move_tactics_unit(board.revision, cell))
        self.assertEqual(board.result, "reached")
        self.assertFalse(board.move_tactics_unit(board.revision, Cell(0, 2, 0)))
        restored = pickle.loads(pickle.dumps(board))
        self.assertEqual(restored.snapshot(), board.snapshot())
        serialized = json.dumps(board.snapshot())
        self.assertNotIn("surface", serialized)

    def test_camera_and_moves_survive_json_and_pickle(self):
        board = BoardSession()
        self.assertTrue(board.set_tactics_view(board.revision, zoom=1.3, rotation=2))
        restored = BoardSession()
        restored.restore(json.loads(json.dumps(board.snapshot())))
        self.assertEqual(restored.snapshot(), board.snapshot())
        self.assertEqual(pickle.loads(pickle.dumps(board)).snapshot(), board.snapshot())

    def test_invalid_restore_does_not_mutate_live_state(self):
        board = BoardSession()
        before = board.snapshot()
        bad = board.snapshot()
        bad["positions"] = [("scout", 99, 99, 99)]
        with self.assertRaises(ValueError):
            board.restore(bad)
        self.assertEqual(board.snapshot(), before)

    def test_stale_controls_cannot_change_reset_board(self):
        board = BoardSession()
        old_revision = board.revision
        self.assertTrue(board.reset_tactics(old_revision))
        self.assertFalse(board.set_tactics_view(old_revision, zoom=1.7))
        self.assertFalse(board.choose(old_revision, "skipped"))
        self.assertEqual(board.tactics_view().zoom, 1.0)

    def test_renderer_gets_private_state(self):
        board = BoardSession()
        state = board.tactics_state()
        state.units[0].cell = GOAL
        self.assertNotEqual(board.tactics_state().units[0].cell, GOAL)

    def test_invalid_view_and_result_are_rejected(self):
        board = BoardSession()
        self.assertFalse(board.set_tactics_view(board.revision, zoom=float("nan")))
        bad = board.snapshot()
        bad["result"] = "reached"
        with self.assertRaises(ValueError):
            board.restore(bad)
