#include <Python.h>
#include <stdlib.h>
#include <math.h>
#include <limits.h>

// --- Hex Utils ---

typedef struct {
    int q;
    int r;
} HexCoord;

static HexCoord offset_to_axial(int col, int row) {
    int q = col - (row - (row & 1)) / 2;
    int r = row;
    return (HexCoord){q, r};
}

static int hex_distance(HexCoord a, HexCoord b) {
    return (abs(a.q - b.q) + abs(a.q + a.r - b.q - b.r) + abs(a.r - b.r)) / 2;
}

// --- Priority Queue ---
typedef struct {
    int x;
    int y;
    double priority;
} Node;

typedef struct {
    Node *nodes;
    int size;
    int capacity;
} MinHeap;

static MinHeap* create_heap(int capacity) {
    MinHeap *heap = (MinHeap*)malloc(sizeof(MinHeap));
    heap->nodes = (Node*)malloc(sizeof(Node) * capacity);
    heap->size = 0;
    heap->capacity = capacity;
    return heap;
}

static void destroy_heap(MinHeap *heap) {
    free(heap->nodes);
    free(heap);
}

static void heap_push(MinHeap *heap, int x, int y, double priority) {
    if (heap->size >= heap->capacity) return;
    
    int i = heap->size++;
    heap->nodes[i] = (Node){x, y, priority};
    
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (heap->nodes[i].priority < heap->nodes[parent].priority) {
            Node temp = heap->nodes[i];
            heap->nodes[i] = heap->nodes[parent];
            heap->nodes[parent] = temp;
            i = parent;
        } else {
            break;
        }
    }
}

static Node heap_pop(MinHeap *heap) {
    if (heap->size == 0) return (Node){-1, -1, -1.0};
    
    Node root = heap->nodes[0];
    heap->nodes[0] = heap->nodes[--heap->size];
    
    int i = 0;
    while (1) {
        int left = 2 * i + 1;
        int right = 2 * i + 2;
        int smallest = i;
        
        if (left < heap->size && heap->nodes[left].priority < heap->nodes[smallest].priority)
            smallest = left;
        if (right < heap->size && heap->nodes[right].priority < heap->nodes[smallest].priority)
            smallest = right;
            
        if (smallest != i) {
            Node temp = heap->nodes[i];
            heap->nodes[i] = heap->nodes[smallest];
            heap->nodes[smallest] = temp;
            i = smallest;
        } else {
            break;
        }
    }
    return root;
}

// --- Common Parser ---
static int parse_common_args(int width, int height, PyObject *terrain_grid_obj, 
                           PyObject *cost_map_obj, PyObject *blockers_list_obj,
                           int **grid_out, double *costs_out, int **blocked_out) {
    
    int map_size = width * height;
    
    // 1. Parse Terrain Grid
    int *grid = (int*)malloc(sizeof(int) * map_size);
    if (!grid) { PyErr_NoMemory(); return 0; }
    
    if (PySequence_Check(terrain_grid_obj)) {
        for (int i = 0; i < map_size; i++) {
            PyObject *item = PySequence_GetItem(terrain_grid_obj, i);
            if (!item) { free(grid); return 0; }
            grid[i] = (int)PyLong_AsLong(item);
            Py_DECREF(item);
        }
    } else {
        free(grid);
        PyErr_SetString(PyExc_TypeError, "terrain_grid must be a sequence");
        return 0;
    }
    
    // 2. Parse Cost Map
    for (int i=0; i<100; i++) costs_out[i] = 1.0;
    
    if (PyDict_Check(cost_map_obj)) {
        PyObject *key, *value;
        Py_ssize_t pos = 0;
        while (PyDict_Next(cost_map_obj, &pos, &key, &value)) {
            long id = PyLong_AsLong(key);
            double cost = PyFloat_AsDouble(value);
            if (id >= 0 && id < 100) {
                costs_out[id] = cost;
            }
        }
    }
    
    // 3. Parse Blockers 
    int *blocked = (int*)calloc(map_size, sizeof(int));
    if (blockers_list_obj && blockers_list_obj != Py_None) {
        PyObject *iterator = PyObject_GetIter(blockers_list_obj);
        if (iterator) {
            PyObject *item;
            while ((item = PyIter_Next(iterator))) {
                if (PyTuple_Check(item) && PyTuple_Size(item) == 2) {
                    int bx = (int)PyLong_AsLong(PyTuple_GetItem(item, 0));
                    int by = (int)PyLong_AsLong(PyTuple_GetItem(item, 1));
                    if (bx >= 0 && bx < width && by >= 0 && by < height) {
                        blocked[by * width + bx] = 1;
                    }
                }
                Py_DECREF(item);
            }
            Py_DECREF(iterator);
        }
    }
    
    *grid_out = grid;
    *blocked_out = blocked;
    return 1;
}

// --- A* Search ---

static PyObject* c_find_path(PyObject* self, PyObject* args) {
    int width, height;
    PyObject *terrain_grid_obj; 
    PyObject *cost_map_obj;     
    int start_x, start_y;
    int end_x, end_y;
    PyObject *blockers_list_obj; 
    double max_cost = -1.0;
    
    if (!PyArg_ParseTuple(args, "iiOO(ii)(ii)Od", 
        &width, &height, &terrain_grid_obj, &cost_map_obj, 
        &start_x, &start_y, &end_x, &end_y, &blockers_list_obj, &max_cost)) {
        return NULL;
    }
    
    int *grid = NULL;
    int *blocked = NULL;
    double costs[100];
    
    if (!parse_common_args(width, height, terrain_grid_obj, cost_map_obj, blockers_list_obj,
                          &grid, costs, &blocked)) {
        return NULL;
    }
    
    int map_size = width * height;
    
    // 4. A* Algorithm
    double *g_scores = (double*)malloc(sizeof(double) * map_size);
    int *parents = (int*)malloc(sizeof(int) * map_size);
    int *in_closed_set = (int*)calloc(map_size, sizeof(int));
    
    for (int i=0; i<map_size; i++) {
        g_scores[i] = INFINITY;
        parents[i] = -1;
    }
    
    int start_idx = start_y * width + start_x;
    int end_idx = end_y * width + end_x;
    int found = 0;
    
    if (start_idx >= 0 && start_idx < map_size) {
        g_scores[start_idx] = 0;
        MinHeap *open_set = create_heap(map_size);
        HexCoord start_hex = offset_to_axial(start_x, start_y);
        HexCoord end_hex = offset_to_axial(end_x, end_y);
        heap_push(open_set, start_x, start_y, (double)hex_distance(start_hex, end_hex));
        
        int even_row_dirs[6][2] = {{-1, -1}, {0, -1}, {1, 0}, {0, 1}, {-1, 1}, {-1, 0}};
        int odd_row_dirs[6][2]  = {{0, -1}, {1, -1}, {1, 0}, {1, 1}, {0, 1}, {-1, 0}};
        
        while (open_set->size > 0) {
            Node current = heap_pop(open_set);
            int cx = current.x;
            int cy = current.y;
            int c_idx = cy * width + cx;
            
            if (cx == end_x && cy == end_y) {
                found = 1;
                break;
            }
            
            if (in_closed_set[c_idx]) continue;
            in_closed_set[c_idx] = 1;
            
            int (*dirs)[2] = (cy % 2 == 0) ? even_row_dirs : odd_row_dirs;
            
            for (int i=0; i<6; i++) {
                int nx = cx + dirs[i][0];
                int ny = cy + dirs[i][1];
                if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;
                
                int n_idx = ny * width + nx;
                if (in_closed_set[n_idx]) continue;
                if (blocked[n_idx]) continue;
                
                int terrain_id = grid[n_idx];
                double move_cost = 1.0;
                if (terrain_id >= 0 && terrain_id < 100) move_cost = costs[terrain_id];
                if (move_cost < 1.0) move_cost = 1.0; 
                if (isinf(move_cost)) continue; 
                
                double tentative_g = g_scores[c_idx] + move_cost;
                if (max_cost >= 0 && tentative_g > max_cost) continue;
                
                if (tentative_g < g_scores[n_idx]) {
                    parents[n_idx] = c_idx;
                    g_scores[n_idx] = tentative_g;
                    double f_score = tentative_g + (double)hex_distance(offset_to_axial(nx, ny), end_hex);
                    heap_push(open_set, nx, ny, f_score);
                }
            }
        }
        destroy_heap(open_set);
    }
    
    PyObject *result_path;
    if (found) {
        result_path = PyList_New(0);
        int curr = end_idx;
        while (curr != start_idx) {
            PyObject *pos = Py_BuildValue("(ii)", curr % width, curr / width);
            PyList_Insert(result_path, 0, pos);
            Py_DECREF(pos);
            curr = parents[curr];
        }
    } else {
        result_path = Py_None;
        Py_INCREF(result_path);
    }
    
    free(grid); free(blocked); free(g_scores); free(parents); free(in_closed_set);
    return result_path;
}

// --- Dijkstra Search (Find All Reachable) ---

static PyObject* c_find_reachable(PyObject* self, PyObject* args) {
    int width, height;
    PyObject *terrain_grid_obj; 
    PyObject *cost_map_obj;     
    int start_x, start_y;
    PyObject *blockers_list_obj; 
    double max_cost;
    PyObject *zoc_map_obj = NULL; // Optional ZOC map
    
    if (!PyArg_ParseTuple(args, "iiOO(ii)Od|O", 
        &width, &height, &terrain_grid_obj, &cost_map_obj, 
        &start_x, &start_y, &blockers_list_obj, &max_cost, &zoc_map_obj)) {
        return NULL;
    }
    
    int *grid = NULL;
    int *blocked = NULL;
    double costs[100];
    
    if (!parse_common_args(width, height, terrain_grid_obj, cost_map_obj, blockers_list_obj,
                          &grid, costs, &blocked)) {
        return NULL;
    }
    
    int map_size = width * height;
    
    // Parse ZOC Map
    int *zoc_map = (int*)calloc(map_size, sizeof(int));
    if (zoc_map_obj && zoc_map_obj != Py_None) {
        if (PySequence_Check(zoc_map_obj)) {
            for (int i = 0; i < map_size; i++) {
                PyObject *item = PySequence_GetItem(zoc_map_obj, i);
                if (item) {
                    zoc_map[i] = PyObject_IsTrue(item);
                    Py_DECREF(item);
                }
            }
        }
    }
    
    double *min_costs = (double*)malloc(sizeof(double) * map_size);
    int *in_closed_set = (int*)calloc(map_size, sizeof(int));
    
    for (int i=0; i<map_size; i++) min_costs[i] = INFINITY;
    
    int start_idx = start_y * width + start_x;
    if (start_idx >= 0 && start_idx < map_size) {
        min_costs[start_idx] = 0;
        MinHeap *queue = create_heap(map_size);
        heap_push(queue, start_x, start_y, 0.0);
        
        int even_row_dirs[6][2] = {{-1, -1}, {0, -1}, {1, 0}, {0, 1}, {-1, 1}, {-1, 0}};
        int odd_row_dirs[6][2]  = {{0, -1}, {1, -1}, {1, 0}, {1, 1}, {0, 1}, {-1, 0}};
        
        while (queue->size > 0) {
            Node current = heap_pop(queue);
            int cx = current.x;
            int cy = current.y;
            int c_idx = cy * width + cx;
            
            // Skip if better path already found
            if (current.priority > min_costs[c_idx]) continue;
            if (in_closed_set[c_idx]) continue;
            in_closed_set[c_idx] = 1;
            
            int (*dirs)[2] = (cy % 2 == 0) ? even_row_dirs : odd_row_dirs;
            
            for (int i=0; i<6; i++) {
                int nx = cx + dirs[i][0];
                int ny = cy + dirs[i][1];
                if (nx < 0 || nx >= width || ny < 0 || ny >= height) continue;
                
                int n_idx = ny * width + nx;
                if (in_closed_set[n_idx]) continue;
                if (blocked[n_idx]) continue;
                
                // ZOC Check: Cannot move from ZOC to non-ZOC (leaving ZOC)
                // Actually, logic is: "Cannot move from ZOC to non-ZOC" based on my previous analysis.
                // Wait, previous analysis: "Once we enter enemy ZOC we cannot leave in the same movement"
                // So if c_idx is ZOC, we cannot move to n_idx unless n_idx is also ZOC?
                // Or rather: if c_idx is ZOC, we STOP.
                // If we stop, we can't expand from c_idx.
                // BUT, if we start in ZOC, we are allowed to move 1 step.
                // So "Stop on enter" means: when moving INTO ZOC, that move is valid, but we don't expand FURTHER.
                
                // Let's implement "Stop on Enter ZOC".
                // If c_idx is ZOC, we can only expand if c_idx is START.
                // But wait, if I move Start -> ZOC1 -> ZOC2?
                // Rules say "Once we enter... cannot leave".
                // And "Units can always move... This allows units to enter ZOC".
                // It usually implies movement ends upon entering ZOC.
                // So if n_idx is ZOC, we can move there, but we shouldn't push n_idx to queue?
                // OR we push it but mark it as "stopped"?
                // If we don't push it, we can't find paths THROUGH it (correct).
                // But we need to record it as reachable.
                
                // Implementation:
                // 1. Calculate cost to n_idx.
                // 2. Record it.
                // 3. Only push to queue if NOT stopping.
                // When do we stop? If n_idx is ZOC.
                // EXCEPT if we are already in ZOC (start in ZOC)?
                // If we start in ZOC, we can move out?
                // The python code says: if from_in_zoc and not to_in_zoc: Block.
                // This means we CAN move ZOC->ZOC.
                
                // Correct Logic based on Python implementation:
                // If (c_idx in ZOC) AND (!n_idx in ZOC): Blocked.
                
                int c_in_zoc = zoc_map[c_idx];
                int n_in_zoc = zoc_map[n_idx];
                
                if (c_in_zoc && !n_in_zoc) continue;
                
                int terrain_id = grid[n_idx];
                double move_cost = 1.0;
                if (terrain_id >= 0 && terrain_id < 100) move_cost = costs[terrain_id];
                if (move_cost < 1.0) move_cost = 1.0; 
                if (isinf(move_cost)) continue; 
                
                double new_cost = min_costs[c_idx] + move_cost;
                if (new_cost > max_cost) continue;
                
                if (new_cost < min_costs[n_idx]) {
                    min_costs[n_idx] = new_cost;
                    heap_push(queue, nx, ny, new_cost);
                }
            }
        }
        destroy_heap(queue);
    }
    
    // Build result dictionary
    PyObject *result_dict = PyDict_New();
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int idx = y * width + x;
            if (min_costs[idx] <= max_cost) {
                PyObject *pos = Py_BuildValue("(ii)", x, y);
                PyObject *cost = PyFloat_FromDouble(min_costs[idx]);
                PyDict_SetItem(result_dict, pos, cost);
                Py_DECREF(pos);
                Py_DECREF(cost);
            }
        }
    }
    
    free(grid); free(blocked); free(min_costs); free(in_closed_set); free(zoc_map);
    return result_dict;
}

static PyMethodDef AlgorithmsMethods[] = {
    {"find_path", c_find_path, METH_VARARGS, "A* pathfinding"},
    {"find_reachable", c_find_reachable, METH_VARARGS, "Dijkstra reachable tiles"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef algorithmsmodule = {
    PyModuleDef_HEAD_INIT,
    "c_algorithms",
    NULL,
    -1,
    AlgorithmsMethods
};

PyMODINIT_FUNC PyInit_c_algorithms(void) {
    return PyModule_Create(&algorithmsmodule);
}