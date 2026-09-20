from docplex.mp.environment import Environment
from docplex.mp.model import Model

Environment().print_information()   # NO debe decir "Community Edition"

m = Model("test_limite")
x = m.integer_var_list(1500, 0, 10, name="x")   # 1500 > 1000: rompe la Community
m.add_constraint(m.sum(x) <= 5000)
m.maximize(m.sum(x))
sol = m.solve()
print("¿Resuelto?", sol is not None, "| objetivo:", m.objective_value)