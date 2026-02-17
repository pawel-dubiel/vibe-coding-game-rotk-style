"""Pytest-wide test environment configuration."""
import os


# Keep test collection/execution headless-safe on CI and local shells without a display/audio device.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
