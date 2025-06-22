from ccmonitor.util import format_time_duration


def test_format_time_duration():
    """Test time duration formatting."""
    assert format_time_duration(30) == "0:30"
    assert format_time_duration(90) == "1:30"
    assert format_time_duration(300) == "5:00"
    assert format_time_duration(9000) == "2:30:00"
    assert format_time_duration(3600) == "1:00:00"
    assert format_time_duration(97200) == "27:00:00"
    assert format_time_duration(172800) == "48:00:00"
