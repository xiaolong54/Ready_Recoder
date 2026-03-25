from gui_state import LogBuffer, NavigationState, ThemeState


def test_theme_state_toggle_and_set_mode():
    state = ThemeState(mode="dark", light_theme="flatly", dark_theme="cyborg")
    assert state.current_theme == "cyborg"

    state.toggle()
    assert state.mode == "light"
    assert state.current_theme == "flatly"

    state.set_mode("dark")
    assert state.current_theme == "cyborg"


def test_navigation_state_switch_and_guard():
    nav = NavigationState(["overview", "rooms", "logs"], "overview")
    assert nav.current == "overview"

    assert nav.switch("logs") is True
    assert nav.current == "logs"

    assert nav.switch("missing") is False
    assert nav.current == "logs"


def test_log_buffer_order_filter_and_limit():
    logs = LogBuffer(max_events=3)
    logs.emit("info", "message-1")
    logs.emit("warn", "message-2")
    logs.emit("error", "message-3")
    logs.emit("info", "message-4")

    drained = logs.drain()
    assert len(drained) == 4
    assert [event.message for event in logs.events] == ["message-2", "message-3", "message-4"]

    errors = logs.filtered("ERROR")
    assert len(errors) == 1
    assert errors[0].message == "message-3"

    recent = logs.recent(2)
    assert [event.message for event in recent] == ["message-3", "message-4"]
