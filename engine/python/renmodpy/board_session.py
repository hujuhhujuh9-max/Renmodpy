"""Saveable native board state, adapted from SDK-/runtime/renfletpy.py.

Ren'Py's owning thread edits this model. No renderers, locks, callbacks or
Android services enter its snapshot.
"""

from dataclasses import asdict, dataclass, replace

from .tactics import PLAYER, TacticsState, TacticsView


@dataclass(frozen=True)
class BoardSnapshot:
    revision: int
    positions: tuple
    selected_unit: str
    view: TacticsView
    selected: str | None
    kind: str = "tactics"


class BoardSession:
    def __init__(self):
        self.revision = 1
        self._state = TacticsState()
        self._state.selected_uid = "scout"
        self._view = TacticsView()
        self.result = None

    def current(self):
        return BoardSnapshot(self.revision, self._state.positions(),
                             self._state.selected_uid, self._view, self.result)

    def tactics_state(self):
        return TacticsState.from_positions(self._state.positions(), self._state.selected_uid)

    def tactics_view(self):
        return self._view

    def set_tactics_view(self, revision, **changes):
        if revision != self.revision or self.result is not None:
            return False
        try:
            view = replace(self._view, **changes)
        except (TypeError, ValueError):
            return False
        if view == self._view:
            return False
        self._view = view
        return True

    def select_tactics_unit(self, revision, uid):
        if revision != self.revision or self.result is not None:
            return False
        unit = next((u for u in self._state.units if u.uid == uid and u.team == PLAYER), None)
        if unit is None or uid == self._state.selected_uid:
            return False
        self._state.select(unit)
        return True

    def move_tactics_unit(self, revision, destination):
        if revision != self.revision or self.result is not None:
            return False
        if not self._state.move_selected(destination):
            return False
        if self._state.goal_reached:
            self.result = "reached"
        return True

    def reset_tactics(self, revision):
        if revision != self.revision or self.result is not None:
            return False
        self._state.reset()
        self._state.selected_uid = "scout"
        self._view = TacticsView()
        self.revision += 1
        return True

    def choose(self, revision, choice_id):
        if revision != self.revision or self.result is not None or choice_id != "skipped":
            return False
        self.result = "skipped"
        return True

    def snapshot(self):
        return {"version": 1, "positions": self._state.positions(),
                "selected_unit": self._state.selected_uid, "view": asdict(self._view),
                "result": self.result}

    def restore(self, data):
        if (not isinstance(data, dict) or type(data.get("version")) is not int
                or data.get("version") != 1 or set(data) !=
                {"version", "positions", "selected_unit", "view", "result"}):
            raise ValueError("Invalid or unsupported RenModPy board save")
        state = TacticsState.from_positions(data["positions"], data["selected_unit"])
        view = TacticsView.from_snapshot(data["view"])
        result = data["result"]
        if (result not in (None, "reached", "skipped")
                or (result == "reached") != state.goal_reached):
            raise ValueError("Invalid RenModPy board result")
        self._state, self._view, self.result = state, view, result
        self.revision += 1

    def __getstate__(self):
        return self.snapshot()

    def __setstate__(self, data):
        self.__init__()
        self.restore(data)
