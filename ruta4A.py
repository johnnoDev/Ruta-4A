import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.animation import FuncAnimation
import requests
import io
from PIL import Image
from math import atan2, degrees


class BusSimulator:
    def __init__(self):
        # Configuración inicial
        plt.style.use('ggplot')
        plt.rcParams['figure.figsize'] = (12, 8)

        # Definir puntos clave
        self.points = {
            'Terminal': (2, 2),
            'Hospital': (8, 5),
            'El Recreo': (5, 8),
            'Barrio Industrial': (10, 2)
        }

        # Definir las rutas
        self.routes = {
            'R1': ['Terminal', 'Hospital'],
            'R2': ['Hospital', 'El Recreo'],
            'R3': ['Terminal', 'El Recreo'],
            'R4': ['Terminal', 'Barrio Industrial']
        }

        # Parámetros de cada ruta
        self.route_params = {
            'R1': {
                'color': 'blue',
                'velocidad_promedio': 30,
                'frecuencia': 15,
                'congestion': 0.7,
                'demanda': 180,
                'buses_requeridos': 180
            },
            'R2': {
                'color': 'green',
                'velocidad_promedio': 25,
                'frecuencia': 20,
                'congestion': 0.6,
                'demanda': 150,
                'buses_requeridos': 150
            },
            'R3': {
                'color': 'red',
                'velocidad_promedio': 35,
                'frecuencia': 25,
                'congestion': 0.4,
                'demanda': 120,
                'buses_requeridos': 120
            },
            'R4': {
                'color': 'purple',
                'velocidad_promedio': 40,
                'frecuencia': 15,
                'congestion': 0.5,
                'demanda': 100,
                'buses_requeridos': 2,
                'impacto_R1': -0.12
            }
        }

        # Inicializar figura
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, 12)
        self.ax.set_ylim(0, 10)
        self.ax.set_aspect('equal')
        self.ax.set_title('Simulación de Autobús - Análisis de Rutas Óptimas (ESPACIO para cambiar)')

        # Cargar imagen de autobús personalizada
        self.load_custom_bus_image()

        # Variables de estado
        self.current_route = 'R1'
        self.bus_pos = {'segment': 0, 'progress': 0}
        self.performance_data = []
        self.system_stability = 0.85

        # Dibujar el mapa inicial
        self.draw_map()

        # Conectar evento de teclado
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)

        # Elementos de texto
        self.create_info_panels()

        # Actualizar texto inicial
        self.update_info_text()

    def load_custom_bus_image(self):
        """Carga la imagen de autobús personalizada"""
        try:
            # Usar la imagen proporcionada
            url = "https://cdn-icons-png.flaticon.com/512/1061/1061186.png"
            response = requests.get(url)
            img = Image.open(io.BytesIO(response.content))

            # Redimensionar manteniendo relación de aspecto
            original_width, original_height = img.size
            new_height = 50
            new_width = int(original_width * (new_height / original_height))

            img = img.resize((new_width, new_height), Image.LANCZOS)
            img = img.convert("RGBA")

            # Procesar transparencia
            data = np.array(img)
            r, g, b, a = data.T

            # Umbral para detectar fondo (ajustar según necesidad)
            background_threshold = 200
            background_areas = (r > background_threshold) & (g > background_threshold) & (b > background_threshold)

            # Hacer fondo transparente
            data[..., :-1][background_areas.T] = (0, 0, 0)
            data[..., -1][background_areas.T] = 0

            # Guardar imagen procesada
            self.bus_img = data
            self.bus_width = new_width / 100  # Ancho relativo para el gráfico
            self.bus_height = new_height / 100  # Alto relativo

            # Mostrar imagen en el gráfico
            self.bus_icon = self.ax.imshow(self.bus_img,
                                           extent=(0, self.bus_width, 0, self.bus_height),
                                           zorder=10)
        except Exception as e:
            print(f"Error cargando imagen personalizada: {e}")
            self.create_fallback_bus_icon()

    def create_fallback_bus_icon(self):
        """Crea un ícono simple si falla la carga de imagen"""
        self.bus_img = np.zeros((50, 100, 4))
        # Cuerpo del autobús (azul)
        self.bus_img[15:35, 10:90, 0] = 0.1
        self.bus_img[15:35, 10:90, 2] = 0.8
        self.bus_img[15:35, 10:90, 3] = 1.0
        # Ventanas (blanco)
        self.bus_img[20:30, 15:85, :3] = 0.9
        self.bus_img[20:30, 15:85, 3] = 1.0
        # Ruedas (negro)
        for x in [25, 75]:
            for y in [35, 40]:
                for i in range(50):
                    for j in range(100):
                        if (i - y) ** 2 + (j - x) ** 2 <= 25:
                            self.bus_img[i, j, :3] = 0.0
                            self.bus_img[i, j, 3] = 1.0

        self.bus_width = 1.0
        self.bus_height = 0.5
        self.bus_icon = self.ax.imshow(self.bus_img,
                                       extent=(0, self.bus_width, 0, self.bus_height),
                                       zorder=10)

    def draw_map(self):
        """Dibuja el mapa con puntos y rutas"""
        # Dibujar puntos clave
        for name, (x, y) in self.points.items():
            self.ax.plot(x, y, 'o', markersize=15, color='black')
            self.ax.text(x, y + 0.4, name, ha='center', fontsize=12, weight='bold')

        # Dibujar todas las rutas (semi-transparentes)
        for route in self.routes:
            points = [self.points[p] for p in self.routes[route]]
            x_coords, y_coords = zip(*points)
            self.ax.plot(x_coords, y_coords, '--',
                         color=self.route_params[route]['color'],
                         alpha=0.3, linewidth=3)

        # Resaltar ruta actual
        self.highlight_current_route()

    def create_info_panels(self):
        """Crea los paneles de información"""
        self.route_text = self.ax.text(0.5, 9.5, "", ha='left', va='top',
                                       bbox=dict(facecolor='white', alpha=0.8))
        self.metrics_text = self.ax.text(7, 9.5, "", ha='left', va='top',
                                         bbox=dict(facecolor='white', alpha=0.8))
        self.impact_text = self.ax.text(4, 0.5, "", ha='center', va='bottom',
                                        bbox=dict(facecolor='white', alpha=0.8))

    def highlight_current_route(self):
        """Resalta la ruta actual"""
        for line in self.ax.lines:
            if line.get_linestyle() == '-':
                line.remove()

        points = [self.points[p] for p in self.routes[self.current_route]]
        x_coords, y_coords = zip(*points)
        self.ax.plot(x_coords, y_coords, '-',
                     color=self.route_params[self.current_route]['color'],
                     alpha=0.8, linewidth=4)

    def on_key_press(self, event):
        """Cambia de ruta cuando se presiona espacio"""
        if event.key == ' ':
            routes = list(self.routes.keys())
            current_idx = routes.index(self.current_route)
            next_idx = (current_idx + 1) % len(routes)
            self.current_route = routes[next_idx]

            self.bus_pos = {'segment': 0, 'progress': 0}
            self.highlight_current_route()
            self.update_info_text()

    def calculate_route_metrics(self, route):
        """Calcula métricas de optimización para una ruta"""
        params = self.route_params[route]
        points = [self.points[p] for p in self.routes[route]]

        distance = np.sqrt((points[1][0] - points[0][0]) ** 2 + (points[1][1] - points[0][1]) ** 2)

        # Ajustar demanda si R4 está activa y es R1
        demanda_ajustada = params['demanda']
        if route == 'R1' and 'R4' in self.routes:
            demanda_ajustada = params['demanda'] * (1 + self.route_params['R4']['impacto_R1'])

        tiempo = (distance / params['velocidad_promedio']) * 60 * (1 + params['congestion'])

        score = (demanda_ajustada * 0.5) / (tiempo * 0.3 + params['frecuencia'] * 0.2)

        return {
            'Ruta': route,
            'Distancia': round(distance, 2),
            'Tiempo': round(tiempo, 2),
            'Congestión': params['congestion'],
            'Frecuencia': params['frecuencia'],
            'Demanda': demanda_ajustada,
            'Puntaje': round(score, 2),
            'Buses': params['buses_requeridos']
        }

    def update_info_text(self):
        """Actualiza los textos informativos"""
        params = self.route_params[self.current_route]
        route_info = (
            f"Ruta actual: {self.current_route} ({' → '.join(self.routes[self.current_route])})\n"
            f"Velocidad: {params['velocidad_promedio']} km/h\n"
            f"Congestión: {params['congestion'] * 100:.0f}%\n"
            f"Frecuencia: {params['frecuencia']} min\n"
            f"Buses: {params['buses_requeridos']}"
        )
        self.route_text.set_text(route_info)

        metrics = self.calculate_route_metrics(self.current_route)
        metrics_info = (
            "Métricas de Optimización:\n"
            f"Distancia: {metrics['Distancia']} km\n"
            f"Tiempo: {metrics['Tiempo']} min\n"
            f"Demanda: {metrics['Demanda']:.0f} buses\n"
            f"Puntaje: {metrics['Puntaje']:.2f}"
        )
        self.metrics_text.set_text(metrics_info)

        impact_info = ""
        if self.current_route in ['R1', 'R4']:
            impacto = self.route_params['R4']['impacto_R1']
            buses_extra = self.route_params['R4']['buses_requeridos']

            if self.current_route == 'R1':
                impact_info = (
                    f"Impacto de R4:\n"
                    f"Reduce demanda en R1: {abs(impacto) * 100:.0f}%\n"
                    f"Buses adicionales necesarios: {buses_extra}"
                )
            else:
                impact_info = (
                    f"Impacto de esta ruta:\n"
                    f"Reduce demanda en R1: {abs(impacto) * 100:.0f}%\n"
                    f"Buses requeridos: {buses_extra}"
                )

        self.impact_text.set_text(impact_info)
        self.performance_data.append(metrics)

    def update_bus_position(self):
        """Actualiza la posición del autobús"""
        points = [self.points[p] for p in self.routes[self.current_route]]
        params = self.route_params[self.current_route]

        speed = 0.01 * (params['velocidad_promedio'] / 30) * (1 - params['congestion'] * 0.5)
        self.bus_pos['progress'] += speed

        if self.bus_pos['progress'] >= 1:
            self.bus_pos['segment'] += 1
            self.bus_pos['progress'] = 0

            if self.bus_pos['segment'] >= len(points) - 1:
                self.bus_pos['segment'] = 0

        segment = self.bus_pos['segment']
        progress = self.bus_pos['progress']
        start = points[segment]
        end = points[segment + 1] if segment + 1 < len(points) else points[0]

        x = start[0] + (end[0] - start[0]) * progress
        y = start[1] + (end[1] - start[1]) * progress

        # Calcular dirección (ángulo en grados)
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        angle = degrees(atan2(dy, dx))

        # Determinar orientación basada en el ángulo
        if -45 <= angle <= 45:  # Movimiento hacia la derecha
            extent = (x - self.bus_width / 2, x + self.bus_width / 2, y, y + self.bus_height)
        elif 45 < angle <= 135:  # Movimiento hacia arriba
            extent = (x - self.bus_height / 2, x + self.bus_height / 2, y, y + self.bus_width)
        elif angle > 135 or angle < -135:  # Movimiento hacia la izquierda
            extent = (x - self.bus_width / 2, x + self.bus_width / 2, y - self.bus_height, y)
        else:  # Movimiento hacia abajo
            extent = (x - self.bus_height / 2, x + self.bus_height / 2, y - self.bus_width, y)

        self.bus_icon.set_extent(extent)

    def update(self, frame):
        """Función de actualización para la animación"""
        self.update_bus_position()
        return [self.bus_icon, self.route_text, self.metrics_text, self.impact_text]

    def run_simulation(self):
        """Ejecuta la simulación"""
        print("Simulación de Autobús con Imagen Personalizada")
        print("=============================================")
        print("Presiona ESPACIO para cambiar de ruta")
        print("Observa las métricas de optimización en tiempo real")

        self.ani = FuncAnimation(self.fig, self.update, frames=None,
                                 interval=50, blit=False, repeat=True)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    simulator = BusSimulator()
    simulator.run_simulation()