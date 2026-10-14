"""Terrain and camera checks retained from the SDK donor."""

import unittest

from renmodpy.tactics import (
    Board, Cell, GOAL, LEVEL_H, TacticsState, TacticsView, build_draw_items,
    camera_bounds, camera_cell, compute_movement_field, point_in_diamond, project,
)

class TerrainTests(unittest.TestCase):
    def test_solids_replace_ground_but_shelves_keep_walkable_floors_underneath(self):
        board = Board()
        self.assertEqual(len(board.surfaces), 43)
        self.assertFalse(board.exists(Cell(3, 2, 0)))
        self.assertEqual([s.cell.z for s in board.surfaces_at(1, 3)], [0, 1, 2])
        self.assertEqual([s.cell.z for s in board.surfaces_at(3, 2)], [1, 2])

    def test_paths_respect_budget_height_and_blocked_units(self):
        board = Board()
        start = Cell(0, 2, 0)
        field = compute_movement_field(board, start, 5, 1, {Cell(3, 2, 1)})
        path = field.path_to(GOAL)
        self.assertEqual((path[0], path[-1]), (start, GOAL))
        self.assertLessEqual(len(path) - 1, 5)
        for a, b in zip(path, path[1:]):
            self.assertEqual(abs(a.x - b.x) + abs(a.y - b.y), 1)
            self.assertLessEqual(abs(a.z - b.z), 1)
            self.assertNotEqual(b, Cell(3, 2, 1))
        no_jump = compute_movement_field(board, start, 5, 0, set())
        self.assertTrue(all(cell.z == 0 for cell in no_jump.cost))
        self.assertEqual(compute_movement_field(board, start, 0, 1, set()).cost, {start: 0})

    def test_only_solid_terrain_has_filled_faces_and_units_stand_above_it(self):
        for rotation in range(4):
            with self.subTest(rotation=rotation):
                items = build_draw_items(TacticsState(), rotation)
                def index(kind, cell):
                    return next(i for i, item in enumerate(items) if item.kind == kind
                                and item.payload.cell == cell)
                self.assertLess(index("terrain", Cell(3, 2, 1)), index("unit", Cell(3, 2, 1)))
                self.assertEqual({item.kind for item in items}, {"terrain", "wall", "marker", "unit"})
                terrain = [item.payload for item in items if item.kind == "terrain"]
                self.assertEqual(len(terrain), 12)
                self.assertTrue(all(surface.kind == "solid" for surface in terrain))
                self.assertTrue(all(surface.cell.z == 1 for surface in terrain))

    def test_every_camera_orientation_keeps_equal_floor_spacing_and_world_identity(self):
        for rotation in range(4):
            for surface in Board().iter_surfaces():
                cell = surface.cell
                self.assertEqual(camera_cell(camera_cell(cell, rotation), -rotation), cell)
                for mode in ("isometric", "side"):
                    low = project(cell, rotation, mode)
                    high = project(Cell(cell.x, cell.y, cell.z + 1), rotation, mode)
                    self.assertEqual(low[0], high[0])
                    self.assertEqual(low[1] - high[1], LEVEL_H)

    def test_top_down_levels_filter_units_and_markers_but_keep_terrain_footprints(self):
        state = TacticsState()
        for level in range(3):
            items = build_draw_items(state, mode="top_down", level=level)
            units = [item.payload for item in items if item.kind == "unit"]
            self.assertEqual({u.uid for u in units},
                             {u.uid for u in state.units if u.cell.z == level})
            self.assertTrue(all(item.payload[0].cell.z == level
                                for item in items if item.kind == "marker"))
            self.assertEqual(sum(item.kind == "terrain" for item in items), 12 if level < 2 else 0)
            self.assertFalse(any(item.kind == "wall" for item in items))
        with self.assertRaises(ValueError):
            build_draw_items(state, mode="top_down")

    def test_top_down_picking_rotates_cells_and_side_view_cannot_choose_a_row(self):
        for rotation in range(4):
            cell = Cell(0, 4, 1)
            x, y = project(cell, rotation, "top_down")
            self.assertTrue(point_in_diamond(x + 24, y, cell, rotation, "top_down"))
            self.assertFalse(point_in_diamond(x + 80, y, cell, rotation, "top_down"))
            self.assertEqual(project(Cell(0, 4, 0), rotation, "top_down"), (x, y))
            x, y = project(cell, rotation, "side")
            self.assertFalse(point_in_diamond(x, y, cell, rotation, "side"))

    def test_side_terrain_rows_merge_into_one_silhouette_without_repeated_alpha_faces(self):
        state = TacticsState()
        for rotation in range(4):
            items = build_draw_items(state, rotation, "side")
            terrain = [item.payload for item in items if item.kind == "terrain"]
            xs = [project(s.cell, rotation, "side")[0] for s in terrain]
            self.assertEqual(len(xs), len(set(xs)))
            self.assertEqual(sum(item.kind == "wall" for item in items), len(xs))
            self.assertFalse(any(item.kind == "marker" and item.payload[1] for item in items))

    def test_camera_fit_contains_every_grid_and_upright_unit_in_all_modes(self):
        for mode in ("isometric", "top_down", "side"):
            left, top, right, bottom = camera_bounds(mode)
            for rotation in range(4):
                for cell in Board().surfaces:
                    x, y = project(cell, rotation, mode)
                    self.assertTrue(left <= x <= right)
                    self.assertTrue(top <= y - (22 if mode == "top_down" else 80) <= y <= bottom)

    def test_rotated_solid_walls_keep_floor_bands_and_shelves_do_not_hide_them(self):
        state = TacticsState()
        state.board.surfaces.clear()
        state.units.clear()
        state.selected_uid = None
        state.board.add(2, 2, 2, "solid")
        for rotation in range(4):
            # An adjacent shelf has air beneath it, so the solid's wall still
            # needs both floor bands even when that shelf faces the camera.
            front = camera_cell(Cell(2, 2, 2), rotation)
            neighbor = camera_cell(Cell(front.x, front.y + 1, 2), -rotation)
            state.board.add(neighbor.x, neighbor.y, 2, "shelf")
            faces = [item.payload for item in build_draw_items(state, rotation)
                     if item.kind == "wall"]
            self.assertEqual(len(faces), 4)
            self.assertTrue(all(face[2][1] - face[1][1] == LEVEL_H for face in faces))
            state.board.surfaces.pop(neighbor)


