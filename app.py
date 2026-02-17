from flask import Flask, render_template, request

from tracker import BlueDartTracker, TrackingError

app = Flask(__name__)
tracker = BlueDartTracker()


@app.get("/")
def index():
    return render_template("index.html", result=None, awb="")


@app.post("/")
def track_awb():
    awb = request.form.get("awb", "").strip()
    if not awb:
        return render_template(
            "index.html",
            awb=awb,
            result={"error": "AWB number zaroori hai. कृपया AWB number daalein."},
        )

    try:
        result = tracker.track_awb(awb)
    except TrackingError as exc:
        result = {
            "awb": awb,
            "error": str(exc),
            "tracking_url": tracker.get_direct_tracking_url(awb),
        }

    return render_template("index.html", awb=awb, result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
