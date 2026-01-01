def hill_climbing(objective_function, initial_state, step_size=0.01, max_iterations=1000):
    """
    Hill Climbing Search Algorithm

    Parameters:
    - objective_function: function to be maximized
    - initial_state: starting value of x
    - step_size: size of change for generating neighbors
    - max_iterations: termination limit

    Returns:
    - best_state: value of x at local maximum
    - best_value: objective function value at best_state
    """

    current_state = initial_state
    current_value = objective_function(current_state)

    for _ in range(max_iterations):

        # Step 02: Generate Neighbors
        neighbors = [
            current_state + step_size,
            current_state - step_size
        ]

        # Step 03: Select Best Neighbor
        neighbor_values = [(n, objective_function(n)) for n in neighbors]
        best_neighbor, best_neighbor_value = max(neighbor_values, key=lambda x: x[1])

        # Step 04: Compare with Current State
        if best_neighbor_value <= current_value:
            break  # Termination condition (local maximum reached)

        current_state = best_neighbor
        current_value = best_neighbor_value

    return current_state, current_value


# Example Objective Function
def f(x):
    return -(x ** 2) + 10 * x  # Concave function with maximum at x=5


# Run Hill Climbing
initial_x = -1
best_x, best_fx = hill_climbing(f, initial_x)

print("Best x:", best_x)
print("f(x):", best_fx)
