from tracker import BlueDartTracker, TrackingError


def test_parse_tracking_html_extracts_status_and_history():
    html = """
    <html><body>
    <div>Current Status: In Transit</div>
    <div>Expected Delivery Date: 12 Feb 2026</div>
    <table>
      <tr><td>10 Feb 2026</td><td>Mumbai Hub</td><td>Shipment Picked Up</td></tr>
      <tr><td>11 Feb 2026</td><td>Pune Hub</td><td>In Transit</td></tr>
    </table>
    </body></html>
    """
    tracker = BlueDartTracker()
    result = tracker.parse_tracking_html(html, "12345678901", "https://example.com")

    assert result.status == "In Transit"
    assert "12 Feb 2026" in result.details
    assert len(result.history) >= 2


def test_parse_tracking_html_raises_for_no_record():
    html = "<html><body>No records found for this AWB</body></html>"
    tracker = BlueDartTracker()

    try:
        tracker.parse_tracking_html(html, "123", "https://example.com")
    except TrackingError as exc:
        assert "record nahi mila" in str(exc)
    else:
        raise AssertionError("TrackingError expected")
