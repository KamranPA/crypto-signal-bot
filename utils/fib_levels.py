# utils/fib_levels.py
def calculate_fib_levels(high, low):
    diff = high - low
    levels = {
        0.0: low,
        0.236: low + 0.236 * diff,
        0.382: low + 0.382 * diff,
        0.5: low + 0.5 * diff,
        0.618: low + 0.618 * diff,
        0.71: low + 0.71 * diff,
        0.786: low + 0.786 * diff,
        1.0: high
    }
    return levels
