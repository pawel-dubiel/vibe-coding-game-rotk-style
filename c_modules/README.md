# C Extensions for Optimization

This directory contains C implementations of performance-critical algorithms (Pathfinding, Hex Math) to significantly improve the game's performance.

## Overview

- **Source File**: `c_algorithms.c`
- **Python Wrapper**: `game/c_pathfinding_wrapper.py`
- **Configuration**: `game/config.py` (Toggle `USE_C_EXTENSIONS`)

When compiled, these extensions provide a **20x-30x speedup** for A* pathfinding compared to the pure Python implementation.

## Prerequisites

To compile the extensions, you need:
1.  **C Compiler**: GCC, Clang, or MSVC.
2.  **Python Development Headers**:
    *   **Linux**: `sudo apt-get install python3-dev` (or equivalent).
    *   **macOS**: Usually included with Xcode Command Line Tools or Homebrew Python.
    *   **Windows**: Automatically handled if you have the correct Visual Studio Build Tools installed.

## How to Compile

Run the following command from the **project root directory**:

```bash
# Build the extension in-place (creates a .so or .pyd file in the root)
python c_modules/setup.py build_ext --inplace
```

After building, you should see a file named `c_algorithms.cpython-XY-platform.so` (Linux/macOS) or `c_algorithms.cpXY-win_amd64.pyd` (Windows) in your root directory.

## Installation / Deployment

For the game to import the module, the compiled shared object file must be in the Python path (e.g., the root directory or the `game/` directory).

If you are distributing this game or setting it up on a new machine, **you must recompile the extension**. The compiled binary is specific to the Operating System, Processor Architecture, and Python version.

## Troubleshooting

### "ModuleNotFoundError: No module named 'c_algorithms'"
1.  Ensure you have compiled the extension using the command above.
2.  Ensure the generated `.so` / `.pyd` file is in the project root (where `main.py` is).
3.  Check `game/config.py` and set `USE_C_EXTENSIONS = False` to temporarily disable it and use the slower Python fallback.

### Compilation Errors
*   **"Python.h not found"**: You are missing Python development headers. Install `python3-dev`.
*   **"Unable to find vcvarsall.bat"** (Windows): You need to install Visual Studio Build Tools with the "Desktop development with C++" workload.

## Architecture

1.  **Data Marshaling**: The Python wrapper (`game/c_pathfinding_wrapper.py`) flattens the game's terrain object into a simple integer array and creates a cost map dictionary.
2.  **C Processing**: The C function receives these flat arrays, performs the heavy pathfinding logic (A* on Hex Grid) using efficient C structs and arrays.
3.  **Result**: The resulting path coordinates are converted back to a Python list of tuples and returned.

This approach minimizes the overhead of crossing the Python/C boundary (Marshaling) while maximizing the speed of the inner loops.
