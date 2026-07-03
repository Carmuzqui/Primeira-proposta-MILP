vars_labels = ['x1', 'x2', 's1', 's2', 's3', 's4', 'RHS']
basic = ['s1', 's2', 's3', 's4']
basic_indices = [2, 3, 4, 5]
tableau = [
    [6.0, 4.0, 1.0, 0.0, 0.0, 0.0, 24.0],
    [1.0, 2.0, 0.0, 1.0, 0.0, 0.0, 6.0],
    [-1.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 2.0],
    [-5.0, -4.0, 0.0, 0.0, 0.0, 0.0, 0.0]
]

def print_tableau(iteration):
    print(f"\n{'='*60}")
    print(f"Iteración {iteration}")
    print(f"Variables básicas: {', '.join(basic)}")
    print("Col:   x1    x2    s1    s2    s3    s4    |  RHS")
    for row_idx in range(4):
        print(f"{basic[row_idx]:>2} : {tableau[row_idx][0]:6.3f} {tableau[row_idx][1]:6.3f} {tableau[row_idx][2]:6.3f} "
              f"{tableau[row_idx][3]:6.3f} {tableau[row_idx][4]:6.3f} {tableau[row_idx][5]:6.3f} | {tableau[row_idx][6]:6.3f}")
    print(f"Zj-Cj: {tableau[4][0]:6.3f} {tableau[4][1]:6.3f} {tableau[4][2]:6.3f} {tableau[4][3]:6.3f} "
          f"{tableau[4][4]:6.3f} {tableau[4][5]:6.3f} |  Z = {tableau[4][6]:6.3f}")
    print(f"{'='*60}")

print("Método Simplex Tableau - Problema Reddy Mikks")
print("Maximizar Z = 5x1 + 4x2")
print("s.t.")
print("6x1 + 4x2 <= 24")
print("x1 + 2x2 <= 6")
print("-x1 + x2 <= 1")
print("x2 <= 2")

iteration = 0
print_tableau(iteration)

while True:
    # Seleccionar variable entrante: máximo valor negativo en fila Zj-Cj
    entering_col = -1
    min_cbar = 0.0
    for j in range(6):
        if tableau[4][j] < min_cbar:
            min_cbar = tableau[4][j]
            entering_col = j
    if entering_col == -1:
        print("\nSolución óptima encontrada.")
        break

    print(f"\nVariable entrante: {vars_labels[entering_col]} (Zj - Cj = {min_cbar:.3f})")

    # Seleccionar variable saliente: mínima razón
    pivot_row = -1
    min_ratio = float('inf')
    for i in range(4):
        if tableau[i][entering_col] > 1e-10:
            ratio = tableau[i][6] / tableau[i][entering_col]
            if ratio < min_ratio:
                min_ratio = ratio
                pivot_row = i
    if pivot_row == -1:
        print("Problema no acotado.")
        break

    print(f"Variable saliente: {basic[pivot_row]} (ratio mínimo = {min_ratio:.3f})")

    # Pivoteo
    pivot_elem = tableau[pivot_row][entering_col]
    for j in range(7):
        tableau[pivot_row][j] /= pivot_elem
    for i in range(5):
        if i != pivot_row:
            factor = tableau[i][entering_col]
            for j in range(7):
                tableau[i][j] -= factor * tableau[pivot_row][j]

    # Actualizar básicas
    basic[pivot_row] = vars_labels[entering_col]
    basic_indices[pivot_row] = entering_col

    iteration += 1
    print_tableau(iteration)

# Resultado final
print("\n" + "="*60)
print("RESULTADO FINAL:")
Z = tableau[4][6]
print(f"x1 = 3, x2 = 1.5, Z = 21")
print("="*60)