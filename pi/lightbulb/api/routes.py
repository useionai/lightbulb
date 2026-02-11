"""REST API routes for LED control."""

import logging
from flask import Blueprint, jsonify, request

from lightbulb.led.controller import LEDController

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


def get_controller() -> LEDController:
    """Get the LED controller singleton."""
    return LEDController()


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "lightbulb"})


@api_bp.route("/leds", methods=["GET"])
def get_leds():
    """Get current LED state."""
    controller = get_controller()
    state = controller.get_state()
    return jsonify(state)


@api_bp.route("/leds/<int:index>", methods=["GET"])
def get_led(index: int):
    """Get a single LED's color.

    Args:
        index: LED index (0-based).
    """
    controller = get_controller()
    try:
        color = controller.get_pixel(index)
        return jsonify({"index": index, **color})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/leds/<int:index>", methods=["PUT"])
def set_led(index: int):
    """Set a single LED's color.

    Args:
        index: LED index (0-based).

    Expected JSON body:
        {"r": 255, "g": 0, "b": 0}
    """
    controller = get_controller()

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    try:
        r = int(data.get("r", 0))
        g = int(data.get("g", 0))
        b = int(data.get("b", 0))

        controller.set_pixel(index, r, g, b)
        return jsonify({"index": index, "r": r, "g": g, "b": b})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting LED {index}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/leds", methods=["PUT"])
def set_all_leds():
    """Set all LEDs to the same color.

    Expected JSON body:
        {"r": 255, "g": 0, "b": 0}
    """
    controller = get_controller()

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    try:
        r = int(data.get("r", 0))
        g = int(data.get("g", 0))
        b = int(data.get("b", 0))

        controller.set_all(r, g, b)
        return jsonify({"r": r, "g": g, "b": b, "message": "All LEDs updated"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting all LEDs: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/scenes", methods=["GET"])
def get_scenes():
    """List all available scenes (static and animated)."""
    controller = get_controller()
    scenes = controller.get_all_scenes()
    state = controller.get_state()
    return jsonify({
        "scenes": scenes,
        "current_scene": state.get("current_scene"),
        "animated": state.get("animated", False),
    })


@api_bp.route("/scenes/<name>", methods=["POST"])
def activate_scene(name: str):
    """Activate a scene by name (static or animated).

    Args:
        name: Scene name.
    """
    controller = get_controller()

    if controller.apply_scene(name):
        state = controller.get_state()
        return jsonify({
            "scene": name,
            "animated": state.get("animated", False),
            "message": f"Scene '{name}' activated",
        })
    else:
        available = controller.get_all_scenes()
        return jsonify({
            "error": f"Scene '{name}' not found",
            "available_scenes": available,
        }), 404


@api_bp.route("/brightness", methods=["GET"])
def get_brightness():
    """Get current brightness level."""
    controller = get_controller()
    state = controller.get_state()
    return jsonify({"brightness": state["brightness"]})


@api_bp.route("/brightness", methods=["PUT"])
def set_brightness():
    """Set brightness level.

    Expected JSON body:
        {"brightness": 128}
    """
    controller = get_controller()

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    try:
        brightness = int(data.get("brightness", 255))
        controller.set_brightness(brightness)
        return jsonify({"brightness": brightness, "message": "Brightness updated"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting brightness: {e}")
        return jsonify({"error": "Internal server error"}), 500
