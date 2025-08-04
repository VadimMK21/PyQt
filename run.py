import numpy as np
import matplotlib.pyplot as plt

# 1. Симуляция системы с ПИД-регулятором
def pid_system(setpoint, Kp, Ki, Kd, T, num_steps):
    t = np.linspace(0, T, num_steps)
    y = np.zeros(num_steps)
    integral_error = 0
    previous_error = 0
    
    for i in range(1, num_steps):
        error = setpoint - y[i-1]
        integral_error += error * (t[i] - t[i-1])
        derivative_error = (error - previous_error) / (t[i] - t[i-1])
        
        # Управляющее воздействие ПИД-регулятора
        u = Kp * error + Ki * integral_error + Kd * derivative_error
        
        # Простая модель системы (например, первого порядка)
        # y_dot = u - y[i-1]
        # y[i] = y[i-1] + y_dot * (t[i] - t[i-1])
        
        # Здесь можно вставить более сложную модель. 
        # Для простоты, давайте смоделируем S-образную кривую, характерную для ПИД-регулятора.
        # Это приближенная симуляция для демонстрации.
        y[i] = y[i-1] + 0.1 * u + np.random.normal(0, 0.01) # Добавляем шум
        
        previous_error = error
    
    return t, y

# Параметры
Kp = 5.0
Ki = 0.5
Kd = 0.2
T = 50
num_steps = 500
setpoint = 1.0

# Моделирование
t, y = pid_system(setpoint, Kp, Ki, Kd, T, num_steps)

# 2. Нахождение точки перегиба (максимум первой производной)
# Вычислим производную с помощью numpy.gradient
y_prime = np.gradient(y, t)
inflection_point_index = np.argmax(y_prime)
x0 = t[inflection_point_index]
y0 = y[inflection_point_index]

# 3. Вычисление уравнения касательной
m = y_prime[inflection_point_index]
tangent = m * (t - x0) + y0

# 4. Построение графика
plt.figure(figsize=(10, 6))
plt.plot(t, y, label='Ответ системы', color='blue')
plt.plot(t, np.full_like(t, setpoint), 'r--', label='Ступенчатое воздействие (Уставка)')
plt.plot(t, tangent, 'g--', label='Касательная в точке перегиба')
plt.scatter(x0, y0, color='red', zorder=5, label='Точка перегиба')
plt.title('График ступенчатого воздействия ПИД-регулятора с касательной')
plt.xlabel('Время')
plt.ylabel('Выход системы')
plt.legend()
plt.grid(True)
plt.show()