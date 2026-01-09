import math


def test_hex_neighbor_distances_flat_top_layout():
    hex_size = 30

    col_spacing = 1.5 * hex_size
    row_spacing = math.sqrt(3) * hex_size
    row_offset = 0.75 * hex_size

    center_x = 1 * col_spacing + row_offset
    center_y = 1 * row_spacing

    east_x = 2 * col_spacing + row_offset
    east_y = 1 * row_spacing
    northeast_x = 2 * col_spacing
    northeast_y = 0 * row_spacing
    northwest_x = 1 * col_spacing
    northwest_y = 0 * row_spacing

    east_dist = math.sqrt((east_x - center_x) ** 2 + (east_y - center_y) ** 2)
    northeast_dist = math.sqrt((northeast_x - center_x) ** 2 + (northeast_y - center_y) ** 2)
    northwest_dist = math.sqrt((northwest_x - center_x) ** 2 + (northwest_y - center_y) ** 2)

    assert math.isclose(east_dist, col_spacing, rel_tol=1e-6, abs_tol=1e-6)
    assert math.isclose(northeast_dist, northwest_dist, rel_tol=1e-6, abs_tol=1e-6)
    assert northeast_dist > east_dist
