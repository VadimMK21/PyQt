import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

class PIDTuner:
    def __init__(self, csv_file, time_col='time', setpoint_col='setpoint', 
                 process_var_col='pv', control_output_col='output'):
        """
        Инициализация PID настройщика
        
        Parameters:
        csv_file: путь к CSV файлу
        time_col: название колонки времени
        setpoint_col: название колонки уставки
        process_var_col: название колонки процессной переменной
        control_output_col: название колонки управляющего воздействия
        """
        self.data = pd.read_csv(csv_file)
        self.time = self.data[time_col].values
        self.setpoint = self.data[setpoint_col].values
        self.pv = self.data[process_var_col].values
        self.output = self.data[control_output_col].values if control_output_col in self.data.columns else None
        
        # Вычисляем ошибку
        self.error = self.setpoint - self.pv
        
        # Результаты настройки
        self.tuning_results = {}
        
    def plot_data(self):
        """Визуализация исходных данных"""
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # График 1: Уставка и процессная переменная
        axes[0].plot(self.time, self.setpoint, 'r--', label='Setpoint', linewidth=2)
        axes[0].plot(self.time, self.pv, 'b-', label='Process Variable', linewidth=1)
        axes[0].set_ylabel('Значение')
        axes[0].set_title('Уставка и процессная переменная')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # График 2: Ошибка
        axes[1].plot(self.time, self.error, 'g-', label='Error (SP - PV)', linewidth=1)
        axes[1].set_ylabel('Ошибка')
        axes[1].set_title('Ошибка регулирования')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        axes[1].axhline(y=0, color='k', linestyle='-', alpha=0.3)
        
        # График 3: Управляющее воздействие (если есть)
        if self.output is not None:
            axes[2].plot(self.time, self.output, 'm-', label='Control Output', linewidth=1)
            axes[2].set_ylabel('Управляющее воздействие')
            axes[2].set_title('Управляющее воздействие')
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)
        else:
            axes[2].text(0.5, 0.5, 'Данные управляющего\nвоздействия отсутствуют', 
                        transform=axes[2].transAxes, ha='center', va='center')
            axes[2].set_title('Управляющее воздействие')
        
        axes[2].set_xlabel('Время')
        plt.tight_layout()
        plt.show()
        
    def identify_step_response(self, start_idx=None, end_idx=None):
        """
        Идентификация переходной характеристики
        Автоматически находит участок с наибольшим изменением уставки
        """
        if start_idx is None or end_idx is None:
            # Автоматический поиск ступенчатого изменения
            setpoint_diff = np.abs(np.diff(self.setpoint))
            step_idx = np.argmax(setpoint_diff)
            
            # Определяем границы анализа
            start_idx = max(0, step_idx - 10)
            end_idx = min(len(self.setpoint), step_idx + 200)
        
        # Извлекаем данные переходного процесса
        t_step = self.time[start_idx:end_idx] - self.time[start_idx]
        sp_step = self.setpoint[start_idx:end_idx]
        pv_step = self.pv[start_idx:end_idx]
        
        # Параметры ступенчатого изменения
        initial_value = np.mean(pv_step[:5])
        step_magnitude = sp_step[-1] - sp_step[0]
        final_value = initial_value + step_magnitude
        
        # Визуализация переходной характеристики
        plt.figure(figsize=(10, 6))
        plt.plot(t_step, sp_step, 'r--', label='Setpoint', linewidth=2)
        plt.plot(t_step, pv_step, 'b-', label='Process Variable', linewidth=2)
        plt.axhline(y=initial_value + 0.632 * step_magnitude, color='g', 
                   linestyle=':', label='63.2% response')
        plt.xlabel('Время')
        plt.ylabel('Значение')
        plt.title('Переходная характеристика')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()
        
        return t_step, pv_step, initial_value, final_value, step_magnitude
    
    def ziegler_nichols_method(self):
        """Метод Циглера-Николса (первый метод - на основе переходной характеристики)"""
        try:
            t_step, pv_step, initial_value, final_value, step_magnitude = self.identify_step_response()
            
            # Находим точку максимальной скорости изменения
            dpv_dt = np.gradient(pv_step, t_step)
            max_slope_idx = np.argmax(np.abs(dpv_dt))
            max_slope = dpv_dt[max_slope_idx]
            
            # Время запаздывания (τ) и постоянная времени (T)
            # Касательная в точке максимального наклона
            t_intersect_initial = (initial_value - pv_step[max_slope_idx]) / max_slope + t_step[max_slope_idx]
            t_intersect_final = (final_value - pv_step[max_slope_idx]) / max_slope + t_step[max_slope_idx]
            
            tau = max(0, t_intersect_initial)  # Время запаздывания
            T = t_intersect_final - t_intersect_initial  # Постоянная времени
            
            if T <= 0 or tau < 0:
                raise ValueError("Некорректные параметры системы")
            
            # Коэффициенты Циглера-Николса
            Kp = 1.2 * T / tau
            Ki = Kp / (2 * tau)
            Kd = Kp * 0.5 * tau
            
            # Расчет Ti и Td
            Ti = Kp / Ki if Ki > 0 else float('inf')  # Время интегрирования
            Td = Kd / Kp if Kp > 0 else 0  # Время дифференцирования
            
            self.tuning_results['Ziegler-Nichols'] = {
                'Kp': Kp, 'Ki': Ki, 'Kd': Kd,
                'Ti': Ti, 'Td': Td,
                'tau': tau, 'T': T,
                'method': 'Ziegler-Nichols (Step Response)'
            }
            
            print(f"Метод Циглера-Николса:")
            print(f"  Время запаздывания (τ): {tau:.3f}")
            print(f"  Постоянная времени (T): {T:.3f}")
            print(f"  Kp: {Kp:.3f}")
            print(f"  Ki: {Ki:.3f}")
            print(f"  Kd: {Kd:.3f}")
            print(f"  Ti (время интегрирования): {Ti:.3f}")
            print(f"  Td (время дифференцирования): {Td:.3f}")
            
            return Kp, Ki, Kd
            
        except Exception as e:
            print(f"Ошибка в методе Циглера-Николса: {e}")
            return None, None, None
    
    def cohen_coon_method(self):
        """Метод Коэна-Куна"""
        try:
            t_step, pv_step, initial_value, final_value, step_magnitude = self.identify_step_response()
            
            # Параметры системы
            dpv_dt = np.gradient(pv_step, t_step)
            max_slope_idx = np.argmax(np.abs(dpv_dt))
            max_slope = dpv_dt[max_slope_idx]
            
            t_intersect_initial = (initial_value - pv_step[max_slope_idx]) / max_slope + t_step[max_slope_idx]
            t_intersect_final = (final_value - pv_step[max_slope_idx]) / max_slope + t_step[max_slope_idx]
            
            tau = max(0, t_intersect_initial)
            T = t_intersect_final - t_intersect_initial
            
            if T <= 0 or tau <= 0:
                raise ValueError("Некорректные параметры системы")
            
            # Соотношение τ/T
            ratio = tau / T
            
            # Коэффициенты Коэна-Куна
            Kp = (1.35 + 0.25 * ratio) * T / tau
            Ki = Kp * (2.5 + 2 * ratio) / (13 + 8 * ratio) / tau
            Kd = Kp * 0.37 * tau / (1 + 0.37 * ratio)
            
            # Расчет Ti и Td
            Ti = Kp / Ki if Ki > 0 else float('inf')  # Время интегрирования
            Td = Kd / Kp if Kp > 0 else 0  # Время дифференцирования
            
            self.tuning_results['Cohen-Coon'] = {
                'Kp': Kp, 'Ki': Ki, 'Kd': Kd,
                'Ti': Ti, 'Td': Td,
                'tau': tau, 'T': T, 'ratio': ratio,
                'method': 'Cohen-Coon'
            }
            
            print(f"\nМетод Коэна-Куна:")
            print(f"  τ/T отношение: {ratio:.3f}")
            print(f"  Kp: {Kp:.3f}")
            print(f"  Ki: {Ki:.3f}")
            print(f"  Kd: {Kd:.3f}")
            print(f"  Ti (время интегрирования): {Ti:.3f}")
            print(f"  Td (время дифференцирования): {Td:.3f}")
            
            return Kp, Ki, Kd
            
        except Exception as e:
            print(f"Ошибка в методе Коэна-Куна: {e}")
            return None, None, None
    
    def simulate_pid(self, Kp, Ki, Kd, dt=None):
        """Симуляция PID регулятора"""
        if dt is None:
            dt = np.mean(np.diff(self.time))
        
        # Инициализация переменных PID
        integral = 0
        prev_error = 0
        output = np.zeros_like(self.error)
        
        for i in range(len(self.error)):
            error = self.error[i]
            
            # Пропорциональная составляющая
            P = Kp * error
            
            # Интегральная составляющая
            integral += error * dt
            I = Ki * integral
            
            # Дифференциальная составляющая
            if i > 0:
                derivative = (error - prev_error) / dt
            else:
                derivative = 0
            D = Kd * derivative
            
            # Общий выход PID
            output[i] = P + I + D
            prev_error = error
        
        return output
    
    def calculate_performance_metrics(self, Kp, Ki, Kd):
        """Расчет показателей качества регулирования"""
        # Симуляция PID
        pid_output = self.simulate_pid(Kp, Ki, Kd)
        
        # Показатели качества
        metrics = {}
        
        # ISE - Integral of Squared Error
        metrics['ISE'] = np.sum(self.error**2) * np.mean(np.diff(self.time))
        
        # IAE - Integral of Absolute Error
        metrics['IAE'] = np.sum(np.abs(self.error)) * np.mean(np.diff(self.time))
        
        # ITAE - Integral of Time-weighted Absolute Error
        metrics['ITAE'] = np.sum(self.time * np.abs(self.error)) * np.mean(np.diff(self.time))
        
        # Максимальное перерегулирование
        if len(self.setpoint) > 0:
            max_overshoot = np.max(self.pv) - np.max(self.setpoint)
            metrics['Max_Overshoot'] = max(0, max_overshoot)
        
        # Среднеквадратичная ошибка
        metrics['RMSE'] = np.sqrt(np.mean(self.error**2))
        
        # Максимальная абсолютная ошибка
        metrics['Max_AE'] = np.max(np.abs(self.error))
        
        return metrics
    
    def optimize_pid_parameters(self, method='ISE', bounds=None):
        """Оптимизация параметров PID с помощью минимизации критерия качества"""
        if bounds is None:
            bounds = [(0.1, 10), (0.01, 5), (0.001, 2)]  # Границы для Kp, Ki, Kd
        
        def objective_function(params):
            Kp, Ki, Kd = params
            try:
                pid_output = self.simulate_pid(Kp, Ki, Kd)
                
                if method == 'ISE':
                    return np.sum(self.error**2)
                elif method == 'IAE':
                    return np.sum(np.abs(self.error))
                elif method == 'ITAE':
                    return np.sum(self.time * np.abs(self.error))
                else:
                    return np.sum(self.error**2)  # По умолчанию ISE
            except:
                return 1e6  # Большое значение при ошибке
        
        # Начальное приближение (если есть результат Циглера-Николса)
        if 'Ziegler-Nichols' in self.tuning_results:
            zn = self.tuning_results['Ziegler-Nichols']
            x0 = [zn['Kp'], zn['Ki'], zn['Kd']]
        else:
            x0 = [1.0, 0.1, 0.01]
        
        # Оптимизация
        result = minimize(objective_function, x0, method='L-BFGS-B', bounds=bounds)
        
        if result.success:
            Kp_opt, Ki_opt, Kd_opt = result.x
            
            # Расчет Ti и Td для оптимизированных параметров
            Ti_opt = Kp_opt / Ki_opt if Ki_opt > 0 else float('inf')
            Td_opt = Kd_opt / Kp_opt if Kp_opt > 0 else 0
            
            self.tuning_results[f'Optimized_{method}'] = {
                'Kp': Kp_opt, 'Ki': Ki_opt, 'Kd': Kd_opt,
                'Ti': Ti_opt, 'Td': Td_opt,
                'method': f'Optimized ({method})',
                'objective_value': result.fun
            }
            
            print(f"\nОптимизированные параметры ({method}):")
            print(f"  Kp: {Kp_opt:.3f}")
            print(f"  Ki: {Ki_opt:.3f}")
            print(f"  Kd: {Kd_opt:.3f}")
            print(f"  Ti (время интегрирования): {Ti_opt:.3f}")
            print(f"  Td (время дифференцирования): {Td_opt:.3f}")
            print(f"  Значение критерия: {result.fun:.3f}")
            
            return Kp_opt, Ki_opt, Kd_opt
        else:
            print(f"Оптимизация не удалась: {result.message}")
            return None, None, None
    
    def display_pid_forms(self):
        """Отображение различных форм записи PID параметров"""
        print("\n" + "="*70)
        print("РАЗЛИЧНЫЕ ФОРМЫ ЗАПИСИ PID ПАРАМЕТРОВ")
        print("="*70)
        
        for method_name, params in self.tuning_results.items():
            if 'Kp' in params:
                Kp, Ki, Kd = params['Kp'], params['Ki'], params['Kd']
                Ti = params.get('Ti', Kp/Ki if Ki > 0 else float('inf'))
                Td = params.get('Td', Kd/Kp if Kp > 0 else 0)
                
                print(f"\n{method_name}:")
                print(f"  Параллельная форма (ISA):")
                print(f"    u(t) = Kp*e(t) + Ki*∫e(t)dt + Kd*de(t)/dt")
                print(f"    Kp = {Kp:.3f}, Ki = {Ki:.3f}, Kd = {Kd:.3f}")
                
                print(f"  Стандартная форма (с Ti, Td):")
                print(f"    u(t) = Kp*(e(t) + (1/Ti)*∫e(t)dt + Td*de(t)/dt)")
                print(f"    Kp = {Kp:.3f}, Ti = {Ti:.3f}, Td = {Td:.3f}")
                
                # Идеальная форма
                if Ti != float('inf') and Ti > 0:
                    print(f"  Идеальная форма:")
                    print(f"    u(t) = Kp*(1 + 1/(Ti*s) + Td*s)*e(s)")
                    print(f"    Kp = {Kp:.3f}, Ti = {Ti:.3f}, Td = {Td:.3f}")
                
                print(f"  Соотношения:")
                print(f"    Ti = Kp/Ki = {Ti:.3f}")
                print(f"    Td = Kd/Kp = {Td:.3f}")
                print("-" * 50)
    def compare_methods(self):
        """Сравнение различных методов настройки"""
        print("\n" + "="*60)
        print("СРАВНЕНИЕ МЕТОДОВ НАСТРОЙКИ PID")
        print("="*60)
        
        comparison_data = []
        
        for method_name, params in self.tuning_results.items():
            if 'Kp' in params:
                Kp, Ki, Kd = params['Kp'], params['Ki'], params['Kd']
                metrics = self.calculate_performance_metrics(Kp, Ki, Kd)
                
                comparison_data.append({
                    'Method': method_name,
                    'Kp': f"{Kp:.3f}",
                    'Ki': f"{Ki:.3f}",
                    'Kd': f"{Kd:.3f}",
                    'Ti': f"{params.get('Ti', 0):.3f}",
                    'Td': f"{params.get('Td', 0):.3f}",
                    'ISE': f"{metrics['ISE']:.3f}",
                    'IAE': f"{metrics['IAE']:.3f}",
                    'RMSE': f"{metrics['RMSE']:.3f}"
                })
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            print(comparison_df.to_string(index=False))
        else:
            print("Нет результатов для сравнения")
    
    def plot_comparison(self):
        """Визуализация сравнения различных методов"""
        if not self.tuning_results:
            print("Нет результатов для визуализации")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        colors = ['blue', 'red', 'green', 'orange', 'purple']
        
        # График оригинальных данных
        axes[0,0].plot(self.time, self.setpoint, 'k--', label='Setpoint', linewidth=2)
        axes[0,0].plot(self.time, self.pv, color='gray', label='Original PV', alpha=0.7)
        
        # Симуляция для каждого метода
        legend_data = []
        performance_data = []
        
        for i, (method_name, params) in enumerate(self.tuning_results.items()):
            if 'Kp' in params and i < len(colors):
                Kp, Ki, Kd = params['Kp'], params['Ki'], params['Kd']
                
                # Симуляция идеального PV (упрощенная)
                pid_output = self.simulate_pid(Kp, Ki, Kd)
                metrics = self.calculate_performance_metrics(Kp, Ki, Kd)
                
                color = colors[i]
                
                # График процессной переменной
                axes[0,0].plot(self.time, self.pv, color=color, 
                              label=f'{method_name}', alpha=0.8)
                
                # График ошибки
                axes[0,1].plot(self.time, self.error, color=color,
                              label=f'{method_name}', alpha=0.8)
                
                # График управляющего воздействия
                axes[1,0].plot(self.time, pid_output, color=color,
                              label=f'{method_name}', alpha=0.8)
                
                legend_data.append(method_name)
                performance_data.append(metrics['ISE'])
        
        # Настройка графиков
        axes[0,0].set_title('Процессная переменная')
        axes[0,0].set_ylabel('Значение')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        axes[0,1].set_title('Ошибка регулирования')
        axes[0,1].set_ylabel('Ошибка')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        axes[1,0].set_title('Управляющее воздействие PID')
        axes[1,0].set_ylabel('Выход PID')
        axes[1,0].set_xlabel('Время')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        
        # График сравнения производительности (ISE)
        if legend_data and performance_data:
            bars = axes[1,1].bar(range(len(legend_data)), performance_data, 
                                color=colors[:len(legend_data)])
            axes[1,1].set_title('Сравнение ISE')
            axes[1,1].set_ylabel('ISE')
            axes[1,1].set_xticks(range(len(legend_data)))
            axes[1,1].set_xticklabels(legend_data, rotation=45, ha='right')
            axes[1,1].grid(True, alpha=0.3)
            
            # Добавляем значения на столбцы
            for bar, value in zip(bars, performance_data):
                axes[1,1].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                              f'{value:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()

def main():
    """Основная функция для демонстрации работы"""
    # Создание примера CSV файла для тестирования
    print("Создание примера данных...")
    
    # Генерация тестовых данных
    t = np.linspace(0, 100, 1000)
    setpoint = np.ones_like(t)
    setpoint[200:] = 2.0  # Ступенчатое изменение уставки
    
    # Симуляция системы первого порядка с запаздыванием
    tau = 5.0  # Постоянная времени
    delay = 2.0  # Запаздывание
    
    # Простая модель системы
    pv = np.zeros_like(t)
    for i in range(1, len(t)):
        dt = t[i] - t[i-1]
        delay_idx = max(0, i - int(delay / dt))
        pv[i] = pv[i-1] + dt/tau * (setpoint[delay_idx] - pv[i-1])
    
    # Добавление шума
    pv += np.random.normal(0, 0.02, len(pv))
    
    # Сохранение в CSV
    test_data = pd.DataFrame({
        'time': t,
        'setpoint': setpoint,
        'pv': pv
    })
    test_data.to_csv('test_pid_data.csv', index=False)
    
    # Использование PID настройщика
    tuner = PIDTuner('test_pid_data.csv')
    
    print("Анализ данных...")
    tuner.plot_data()
    
    print("Настройка PID параметров...")
    tuner.ziegler_nichols_method()
    tuner.cohen_coon_method()
    tuner.optimize_pid_parameters('ISE')
    tuner.optimize_pid_parameters('IAE')
    
    print("\nРазличные формы записи PID:")
    tuner.display_pid_forms()
    
    print("\nСравнение методов:")
    tuner.compare_methods()
    
    print("\nВизуализация сравнения:")
    tuner.plot_comparison()

if __name__ == "__main__":
    main()