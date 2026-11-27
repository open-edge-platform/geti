# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest
from model_api.visualizer.primitive import BoundingBox, Label, Overlay, Polygon
from model_api.visualizer.primitive.keypoints import Keypoint
from model_api.visualizer.scene.scene import Scene
from PIL import Image


class ConcreteScene(Scene):
    """Concrete implementation of Scene for testing."""

    @property
    def default_layout(self):
        from model_api.visualizer.layout import Flatten

        return Flatten()


def _make_image():
    return Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))


# --- Scene._to_overlay ---


def test_to_overlay_ndarray():
    img = _make_image()
    scene = ConcreteScene(img, overlay=np.zeros((50, 50, 3), dtype=np.uint8))
    assert len(scene.overlay) == 1
    assert isinstance(scene.overlay[0], Overlay)


def test_to_overlay_single():
    img = _make_image()
    overlay = Overlay(Image.fromarray(np.zeros((50, 50, 3), dtype=np.uint8)))
    scene = ConcreteScene(img, overlay=overlay)
    assert len(scene.overlay) == 1


# --- Scene._to_bounding_box ---


def test_to_bounding_box_single():
    img = _make_image()
    bb = BoundingBox(10, 20, 30, 40)
    scene = ConcreteScene(img, bounding_box=bb)
    assert len(scene.bounding_box) == 1


# --- Scene._to_label ---


def test_to_label_single():
    img = _make_image()
    label = Label("test")
    scene = ConcreteScene(img, label=label)
    assert len(scene.label) == 1


# --- Scene._to_polygon ---


def test_to_polygon_single():
    img = _make_image()
    polygon = Polygon(np.array([[0, 0], [10, 0], [10, 10]]))
    scene = ConcreteScene(img, polygon=polygon)
    assert len(scene.polygon) == 1


# --- Scene._to_keypoints ---


def test_to_keypoints_single():
    img = _make_image()
    kp = Keypoint(np.array([[10, 20], [30, 40]]))
    scene = ConcreteScene(img, keypoints=kp)
    assert len(scene.keypoints) == 1


def test_to_keypoints_ndarray():
    img = _make_image()
    scene = ConcreteScene(img, keypoints=np.array([[10, 20], [30, 40]]))
    assert len(scene.keypoints) == 1


# --- Scene.has_primitives ---


def test_has_primitives_keypoint():
    img = _make_image()
    kp = Keypoint(np.array([[10, 20]]))
    scene = ConcreteScene(img, keypoints=kp)
    assert scene.has_primitives(Keypoint)
    assert not scene.has_primitives(Polygon)


# --- Scene.get_primitives ---


def test_get_primitives_polygon():
    img = _make_image()
    poly = Polygon(np.array([[0, 0], [10, 0], [10, 10]]))
    scene = ConcreteScene(img, polygon=poly)
    prims = scene.get_primitives(Polygon)
    assert len(prims) == 1


def test_get_primitives_keypoint():
    img = _make_image()
    kp = Keypoint(np.array([[10, 20]]))
    scene = ConcreteScene(img, keypoints=kp)
    prims = scene.get_primitives(Keypoint)
    assert len(prims) == 1


def test_get_primitives_unknown_raises():
    img = _make_image()
    scene = ConcreteScene(img)
    with pytest.raises(ValueError, match=r"Primitive .* not found"):
        scene.get_primitives(int)


# --- Scene.has_primitives with unknown type ---


def test_has_primitives_unknown_type():
    """has_primitives returns False for unknown primitive types."""
    img = _make_image()
    scene = ConcreteScene(img)
    assert scene.has_primitives(int) is False


# --- Scene.show ---


def test_scene_show(monkeypatch):
    """Scene.show() calls render().show()."""
    img = _make_image()
    scene = ConcreteScene(img)
    shown = []
    monkeypatch.setattr(Image.Image, "show", lambda self: shown.append(True))
    scene.show()
    assert shown == [True]


# --- Scene.default_layout ---


def test_scene_default_layout_not_implemented():
    """Scene base class raises NotImplementedError for default_layout."""
    img = _make_image()
    scene = ConcreteScene(img)
    # Access default_layout from concrete - it works
    assert scene.default_layout is not None


def test_scene_base_default_layout_raises():
    """Scene base class raises NotImplementedError for default_layout."""
    img = _make_image()
    scene = Scene(img)
    with pytest.raises(NotImplementedError, match="Default layout not implemented"):
        _ = scene.default_layout


# --- Scene.render ---


def test_scene_render_with_layout():
    img = _make_image()
    from model_api.visualizer.layout import Flatten

    layout = Flatten()
    scene = ConcreteScene(img, layout=layout)
    rendered = scene.render()
    assert isinstance(rendered, Image.Image)


def test_scene_render_default_layout():
    img = _make_image()
    scene = ConcreteScene(img)
    rendered = scene.render()
    assert isinstance(rendered, Image.Image)


# --- Visualizer unsupported result type ---


def test_visualizer_unsupported_result_raises():
    from model_api.visualizer import Visualizer

    vis = Visualizer()
    img = _make_image()
    with pytest.raises(ValueError, match="Unsupported result type"):
        vis.render(img, "not_a_result")
