import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import subprocess
import tempfile
import threading
import queue
import time

class MinExtGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto MinExt - Minimizar Extremismo en Poblaciones")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Variables para almacenar rutas de archivos
        self.archivo_entrada = None
        self.archivo_modelo = None
        
        # Cola para comunicación entre hilos
        self.mensaje_queue = queue.Queue()
        
        # Variable para controlar el proceso en ejecución
        self.proceso_activo = None
        self.hilo_activo = None
        
        self.crear_interfaz()
        self.iniciar_monitor_cola()
    
    def crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        titulo = ttk.Label(main_frame, text="Proyecto MinExt", 
                          font=("Arial", 16, "bold"))
        titulo.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Sección de archivos
        archivos_frame = ttk.LabelFrame(main_frame, text="Configuración de Archivos", padding="10")
        archivos_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        archivos_frame.columnconfigure(1, weight=1)
        
        # Archivo de entrada
        ttk.Label(archivos_frame, text="Archivo de entrada (.txt):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.entrada_path = tk.StringVar()
        entrada_entry = ttk.Entry(archivos_frame, textvariable=self.entrada_path, state="readonly")
        entrada_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=(0, 5))
        ttk.Button(archivos_frame, text="Buscar", 
                  command=self.seleccionar_archivo_entrada).grid(row=0, column=2, pady=(0, 5))
        
        # Archivo del modelo
        ttk.Label(archivos_frame, text="Archivo modelo (.mzn):").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.modelo_path = tk.StringVar()
        modelo_entry = ttk.Entry(archivos_frame, textvariable=self.modelo_path, state="readonly")
        modelo_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=(0, 5))
        ttk.Button(archivos_frame, text="Buscar", 
                  command=self.seleccionar_archivo_modelo).grid(row=1, column=2, pady=(0, 5))
        
        # Frame de configuración avanzada
        config_frame = ttk.LabelFrame(main_frame, text="Configuración Avanzada", padding="10")
        config_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Timeout
        ttk.Label(config_frame, text="Timeout (segundos):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.timeout_var = tk.StringVar(value="300")  # 5 minutos por defecto
        timeout_entry = ttk.Entry(config_frame, textvariable=self.timeout_var, width=10)
        timeout_entry.grid(row=0, column=1, sticky=tk.W)
        
        # Solver
        ttk.Label(config_frame, text="Solver:").grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        self.solver_var = tk.StringVar(value="Gecode")
        solver_combo = ttk.Combobox(config_frame, textvariable=self.solver_var, 
                                   values=["Gecode", "Chuffed", "COIN-BC", "OR-Tools"], 
                                   state="readonly", width=12)
        solver_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Número de hilos
        ttk.Label(config_frame, text="Hilos:").grid(row=0, column=4, sticky=tk.W, padx=(20, 10))
        self.threads_var = tk.StringVar(value="auto")
        threads_entry = ttk.Entry(config_frame, textvariable=self.threads_var, width=8)
        threads_entry.grid(row=0, column=5, sticky=tk.W)
        
        # Botones principales
        ejecutar_frame = ttk.Frame(main_frame)
        ejecutar_frame.grid(row=3, column=0, columnspan=3, pady=(10, 20))
        
        self.btn_ejecutar = ttk.Button(ejecutar_frame, text="Ejecutar Modelo MinExt", 
                                      command=self.ejecutar_modelo, style="Accent.TButton")
        self.btn_ejecutar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_cancelar = ttk.Button(ejecutar_frame, text="Cancelar", 
                                      command=self.cancelar_ejecucion, state='disabled')
        self.btn_cancelar.pack(side=tk.LEFT)
        
        # Progress bar con información
        progress_frame = ttk.Frame(ejecutar_frame)
        progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X)
        
        self.status_label = ttk.Label(progress_frame, text="Listo para ejecutar")
        self.status_label.pack(pady=(5, 0))
        
        # Área de resultados
        resultados_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        resultados_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        resultados_frame.columnconfigure(0, weight=1)
        resultados_frame.rowconfigure(0, weight=1)
        
        self.texto_resultados = scrolledtext.ScrolledText(resultados_frame, 
                                                         wrap=tk.WORD, 
                                                         height=20, 
                                                         font=("Consolas", 10))
        self.texto_resultados.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame para botones adicionales
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(botones_frame, text="Limpiar Resultados", 
                  command=self.limpiar_resultados).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(botones_frame, text="Guardar Resultados", 
                  command=self.guardar_resultados).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(botones_frame, text="Convertir TXT → DZN", 
                  command=self.convertir_archivos).pack(side=tk.LEFT)
        
        # Configurar weights para redimensionamiento
        main_frame.rowconfigure(4, weight=1)
    
    def iniciar_monitor_cola(self):
        """Monitorea la cola de mensajes y actualiza la interfaz"""
        try:
            while True:
                mensaje_tipo, contenido = self.mensaje_queue.get_nowait()
                
                if mensaje_tipo == "texto":
                    self.texto_resultados.insert(tk.END, contenido)
                    self.texto_resultados.see(tk.END)
                elif mensaje_tipo == "status":
                    self.status_label.config(text=contenido)
                elif mensaje_tipo == "finalizar":
                    self.finalizar_ejecucion()
                elif mensaje_tipo == "error":
                    messagebox.showerror("Error", contenido)
                    self.finalizar_ejecucion()
                    
        except queue.Empty:
            pass
        
        # Programar la próxima verificación
        self.root.after(100, self.iniciar_monitor_cola)
    
    def seleccionar_archivo_entrada(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo de entrada",
            filetypes=[("Archivos de texto", "*.txt"), ("Archivos MinExt", "*.mext"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            self.archivo_entrada = archivo
            self.entrada_path.set(archivo)
    
    def seleccionar_archivo_modelo(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo del modelo MiniZinc",
            filetypes=[("Archivos MiniZinc", "*.mzn"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            self.archivo_modelo = archivo
            self.modelo_path.set(archivo)
    
    def convertir_contenido_txt_a_dzn(self, contenido_txt):
        """Convierte el contenido de un archivo TXT al formato DZN"""
        lineas = contenido_txt.strip().split("\n")
        
        if len(lineas) < 7:
            raise ValueError("El archivo no tiene el formato correcto. Debe tener al menos 7 líneas.")
        
        num_personas = lineas[0].strip()
        num_opiniones = int(lineas[1].strip())
        distribucion_inicial = lineas[2].strip()
        valores_extremismo = lineas[3].strip()
        costos_extra = lineas[4].strip()
        
        # Verificar que hay suficientes líneas para la matriz de costos
        if len(lineas) < 5 + num_opiniones + 2:
            raise ValueError(f"El archivo debe tener al menos {5 + num_opiniones + 2} líneas.")
        
        matriz_costos_lineas = lineas[5:5 + num_opiniones]
        costo_maximo = lineas[5 + num_opiniones].strip()
        movimientos_maximos = lineas[6 + num_opiniones].strip()

        dzn = []
        dzn.append(f"num_personas = {num_personas};")
        dzn.append(f"num_opiniones = {num_opiniones};")
        dzn.append(f"distribucion_inicial = [{distribucion_inicial}];")
        dzn.append(f"valores_extremismo = [{valores_extremismo}];")
        dzn.append(f"costos_extra = [{costos_extra}];")

        dzn.append("matriz_costos = [")
        for i, fila in enumerate(matriz_costos_lineas):
            fila_str = "[" + fila.strip() + "]"
            dzn.append("  " + fila_str + ("," if i < len(matriz_costos_lineas)-1 else ""))
        dzn.append("];")

        dzn.append(f"costo_maximo = {costo_maximo};")
        dzn.append(f"movimientos_maximos = {movimientos_maximos};")

        return "\n".join(dzn)
    
    def ejecutar_modelo_thread(self):
        """Ejecuta el modelo en un hilo separado con optimizaciones"""
        temp_dzn_path = None
        start_time = time.time()
        
        try:
            # Validar archivos
            if not self.archivo_entrada or not os.path.exists(self.archivo_entrada):
                self.mensaje_queue.put(("error", f"Por favor selecciona un archivo de entrada válido.\nArchivo: {self.archivo_entrada}"))
                return

            if not self.archivo_modelo or not os.path.exists(self.archivo_modelo):
                self.mensaje_queue.put(("error", f"Por favor selecciona un archivo de modelo válido.\nArchivo: {self.archivo_modelo}"))
                return

            # Actualizar status
            self.mensaje_queue.put(("status", "Leyendo archivos..."))
            
            # Leer archivo de entrada
            with open(self.archivo_entrada, 'r', encoding='utf-8') as f:
                contenido_entrada = f.read()

            # Convertir a formato DZN
            self.mensaje_queue.put(("status", "Convirtiendo formato..."))
            contenido_dzn = self.convertir_contenido_txt_a_dzn(contenido_entrada)

            # Crear archivo temporal DZN
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dzn', delete=False, encoding='utf-8') as temp_dzn:
                temp_dzn.write(contenido_dzn)
                temp_dzn_path = temp_dzn.name

            # Mostrar información inicial
            self.mensaje_queue.put(("texto", f"=== EJECUTANDO MODELO MINEXT ===\n"))
            self.mensaje_queue.put(("texto", f"Inicio: {time.strftime('%H:%M:%S')}\n"))
            self.mensaje_queue.put(("texto", f"Archivo de entrada: {os.path.basename(self.archivo_entrada)}\n"))
            self.mensaje_queue.put(("texto", f"Archivo de modelo: {os.path.basename(self.archivo_modelo)}\n"))

            # Construir comando optimizado
            cmd = ['minizinc']
            
            # Añadir solver
            solver = self.solver_var.get()
            cmd.extend(['--solver', solver])
            
            # Añadir configuración de hilos
            threads = self.threads_var.get().strip()
            if threads and threads.lower() != 'auto':
                try:
                    thread_num = int(threads)
                    if thread_num > 0:
                        cmd.extend(['-p', str(thread_num)])
                except ValueError:
                    pass
            
            # Añadir timeout
            try:
                timeout_val = int(self.timeout_var.get())
                if timeout_val > 0:
                    cmd.extend(['--time-limit', str(timeout_val * 1000)])  # MiniZinc usa milisegundos
            except ValueError:
                pass
            
            # Optimizaciones adicionales
            cmd.extend([
                '--statistics',  # Mostrar estadísticas
                '--verbose-solving'  # Información del proceso de resolución
            ])
            
            # Añadir archivos
            cmd.extend([self.archivo_modelo, temp_dzn_path])

            self.mensaje_queue.put(("texto", f"Solver: {solver}\n"))
            self.mensaje_queue.put(("texto", f"Comando: {' '.join(cmd)}\n\n"))
            self.mensaje_queue.put(("status", f"Resolviendo con {solver}..."))

            # Ejecutar MiniZinc con comunicación en tiempo real
            self.proceso_activo = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                bufsize=1,  # Buffer de línea para salida inmediata
                universal_newlines=True
            )

            # Leer salida en tiempo real
            stdout_lines = []
            stderr_lines = []
            
            # Leer stdout
            while True:
                if self.proceso_activo.poll() is not None:
                    break
                
                try:
                    line = self.proceso_activo.stdout.readline()
                    if line:
                        stdout_lines.append(line)
                        # Mostrar líneas importantes inmediatamente
                        if any(keyword in line.lower() for keyword in ['extremismo', 'costo', 'movimientos', 'resultado']):
                            self.mensaje_queue.put(("texto", line))
                except:
                    break
            
            # Obtener salida restante
            remaining_stdout, stderr = self.proceso_activo.communicate()
            if remaining_stdout:
                stdout_lines.append(remaining_stdout)
            if stderr:
                stderr_lines.append(stderr)
            
            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines)
            
            elapsed_time = time.time() - start_time

            # Mostrar resultados
            if self.proceso_activo.returncode == 0:
                self.mensaje_queue.put(("texto", f"\n=== RESULTADOS ({elapsed_time:.2f}s) ===\n"))
                self.mensaje_queue.put(("texto", stdout))
                if stderr:
                    self.mensaje_queue.put(("texto", "\n=== INFORMACIÓN DEL SOLVER ===\n"))
                    self.mensaje_queue.put(("texto", stderr))
                self.mensaje_queue.put(("status", f"Completado en {elapsed_time:.2f}s"))
            else:
                error_msg = stderr if stderr else stdout
                self.mensaje_queue.put(("texto", f"\n=== ERROR ({elapsed_time:.2f}s) ===\n"))
                self.mensaje_queue.put(("texto", error_msg))
                self.mensaje_queue.put(("status", "Error en la ejecución"))

        except Exception as e:
            elapsed_time = time.time() - start_time
            self.mensaje_queue.put(("error", f"Error durante la ejecución ({elapsed_time:.2f}s):\n{str(e)}"))

        finally:
            # Limpiar archivo temporal
            if temp_dzn_path and os.path.exists(temp_dzn_path):
                try:
                    os.unlink(temp_dzn_path)
                except:
                    pass

            # Limpiar proceso
            self.proceso_activo = None
            self.mensaje_queue.put(("finalizar", None))
    
    def cancelar_ejecucion(self):
        """Cancela la ejecución actual"""
        if self.proceso_activo:
            try:
                self.proceso_activo.terminate()
                self.mensaje_queue.put(("texto", "\n=== EJECUCIÓN CANCELADA ===\n"))
                self.mensaje_queue.put(("status", "Cancelado por el usuario"))
            except:
                pass
        
        if self.hilo_activo and self.hilo_activo.is_alive():
            # El hilo se detendrá cuando detecte que el proceso fue terminado
            pass
    
    def finalizar_ejecucion(self):
        """Finaliza la ejecución y restaura el estado de la interfaz"""
        self.progress.stop()
        self.btn_ejecutar.config(state='normal')
        self.btn_cancelar.config(state='disabled')
        self.proceso_activo = None
        self.hilo_activo = None
    
    def ejecutar_modelo(self):
        # Validar configuración
        try:
            timeout_val = int(self.timeout_var.get())
            if timeout_val <= 0:
                messagebox.showerror("Error", "El timeout debe ser un número positivo.")
                return
        except ValueError:
            messagebox.showerror("Error", "El timeout debe ser un número válido.")
            return
        
        # Deshabilitar botón y mostrar progreso
        self.btn_ejecutar.config(state='disabled')
        self.btn_cancelar.config(state='normal')
        self.progress.start()
        self.status_label.config(text="Iniciando...")
        
        # Ejecutar en hilo separado
        self.hilo_activo = threading.Thread(target=self.ejecutar_modelo_thread)
        self.hilo_activo.daemon = True
        self.hilo_activo.start()
    
    def limpiar_resultados(self):
        self.texto_resultados.delete(1.0, tk.END)
        self.status_label.config(text="Listo para ejecutar")
    
    def guardar_resultados(self):
        contenido = self.texto_resultados.get(1.0, tk.END)
        if contenido.strip():
            archivo = filedialog.asksaveasfilename(
                title="Guardar resultados",
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
            )
            if archivo:
                try:
                    with open(archivo, 'w', encoding='utf-8') as f:
                        f.write(contenido)
                    messagebox.showinfo("Éxito", "Resultados guardados correctamente.")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        else:
            messagebox.showwarning("Advertencia", "No hay resultados para guardar.")
    
    def convertir_archivos(self):
        """Función para convertir archivos TXT a DZN"""
        archivos = filedialog.askopenfilenames(
            title="Selecciona los archivos .txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Archivos MinExt", "*.mext")]
        )

        if not archivos:
            return

        carpeta_salida = filedialog.askdirectory(title="Selecciona la carpeta de destino")
        if not carpeta_salida:
            return

        convertidos = 0
        for ruta in archivos:
            try:
                with open(ruta, "r", encoding='utf-8') as archivo:
                    contenido = archivo.read()
                contenido_dzn = self.convertir_contenido_txt_a_dzn(contenido)

                nombre_base = os.path.splitext(os.path.basename(ruta))[0]
                ruta_salida = os.path.join(carpeta_salida, nombre_base + ".dzn")

                with open(ruta_salida, "w", encoding='utf-8') as salida:
                    salida.write(contenido_dzn)
                
                convertidos += 1

            except Exception as e:
                messagebox.showerror("Error", f"Error con el archivo {ruta}:\n{str(e)}")
                return

        messagebox.showinfo("Conversión exitosa", f"{convertidos} archivos convertidos correctamente.")

def main():
    root = tk.Tk()
    
    # Configurar estilo
    style = ttk.Style()
    
    # Intentar usar un tema moderno
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'vista' in available_themes:
        style.theme_use('vista')
    
    app = MinExtGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()