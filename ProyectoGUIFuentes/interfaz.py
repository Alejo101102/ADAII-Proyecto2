import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import subprocess
import tempfile
import threading
import queue
import time
import re

class MinExtGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto MinExt - Minimizar Extremismo en Poblaciones")
        self.root.geometry("1000x800")
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
        ttk.Label(archivos_frame, text="Archivo de entrada (.txt/.mext):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
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
        self.timeout_var = tk.StringVar(value="300")  
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
        
        # Notebook para pestañas de resultados
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Pestaña de resultados sin procesar
        raw_frame = ttk.Frame(notebook, padding="10")
        notebook.add(raw_frame, text="Salida Completa")
        raw_frame.columnconfigure(0, weight=1)
        raw_frame.rowconfigure(0, weight=1)
        
        self.texto_resultados = scrolledtext.ScrolledText(raw_frame, 
                                                         wrap=tk.WORD, 
                                                         height=18, 
                                                         font=("Consolas", 10))
        self.texto_resultados.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Pestaña de resultados procesados
        processed_frame = ttk.Frame(notebook, padding="10")
        notebook.add(processed_frame, text="Resultados Procesados")
        processed_frame.columnconfigure(0, weight=1)
        processed_frame.rowconfigure(0, weight=1)
        
        self.texto_procesado = scrolledtext.ScrolledText(processed_frame, 
                                                        wrap=tk.WORD, 
                                                        height=18, 
                                                        font=("Arial", 11))
        self.texto_procesado.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame para botones adicionales
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(botones_frame, text="Limpiar Resultados", 
                  command=self.limpiar_resultados).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(botones_frame, text="Guardar Resultados", 
                  command=self.guardar_resultados).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(botones_frame, text="Convertir TXT → DZN", 
                  command=self.convertir_archivos).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(botones_frame, text="Validar Entrada", 
                  command=self.validar_entrada_manual).pack(side=tk.LEFT)
        
        # Configurar weights para redimensionamiento
        main_frame.rowconfigure(4, weight=1)
    
    def validar_formato_entrada(self, contenido):
        """Validar que el archivo tenga el formato correcto según la Sección 3.1"""
        try:
            lineas = contenido.strip().split("\n")
            
            if len(lineas) < 7:
                return False, "El archivo debe tener al menos 7 líneas"
            
            # número de personas (n)
            try:
                n = int(lineas[0].strip())
                if n <= 0:
                    return False, "El número de personas debe ser positivo"
            except ValueError:
                return False, "La primera línea debe contener un número entero (número de personas)"
            
            # número de opiniones (m)
            try:
                m = int(lineas[1].strip())
                if m <= 0:
                    return False, "El número de opiniones debe ser positivo"
            except ValueError:
                return False, "La segunda línea debe contener un número entero (número de opiniones)"
            
            # Verificar que hay suficientes líneas
            lineas_esperadas = 5 + m + 2  # 5 líneas iniciales + m líneas de matriz + 2 líneas finales
            if len(lineas) < lineas_esperadas:
                return False, f"El archivo debe tener {lineas_esperadas} líneas para {m} opiniones. Encontradas: {len(lineas)}"
            
            # distribución inicial
            try:
                distribucion = [int(x.strip()) for x in lineas[2].split(',')]
                if len(distribucion) != m:
                    return False, f"La distribución inicial debe tener {m} valores, encontrados {len(distribucion)}"
                if sum(distribucion) != n:
                    return False, f"La suma de la distribución inicial ({sum(distribucion)}) debe ser igual al número de personas ({n})"
                if any(x < 0 for x in distribucion):
                    return False, "Los valores de distribución no pueden ser negativos"
            except ValueError:
                return False, "Error en el formato de la distribución inicial (línea 3)"
            
            # valores de extremismo
            try:
                extremismo = [float(x.strip()) for x in lineas[3].split(',')]
                if len(extremismo) != m:
                    return False, f"Los valores de extremismo deben ser {m}, encontrados {len(extremismo)}"
                if any(x < 0 or x > 1 for x in extremismo):
                    return False, "Los valores de extremismo deben estar entre 0 y 1"
            except ValueError:
                return False, "Error en el formato de los valores de extremismo (línea 4)"
            
            # costos extra
            try:
                costos_extra = [float(x.strip()) for x in lineas[4].split(',')]
                if len(costos_extra) != m:
                    return False, f"Los costos extra deben ser {m}, encontrados {len(costos_extra)}"
                if any(x < 0 for x in costos_extra):
                    return False, "Los costos extra no pueden ser negativos"
            except ValueError:
                return False, "Error en el formato de los costos extra (línea 5)"
            
            # matriz de costos
            for i in range(m):
                try:
                    fila = [float(x.strip()) for x in lineas[5 + i].split(',')]
                    if len(fila) != m:
                        return False, f"La fila {i+1} de la matriz de costos debe tener {m} valores, encontrados {len(fila)}"
                    if any(x < 0 for x in fila):
                        return False, f"Los costos en la fila {i+1} no pueden ser negativos"
                    if fila[i] != 0:
                        return False, f"El costo de la opinión {i+1} a sí misma debe ser 0"
                except ValueError:
                    return False, f"Error en el formato de la fila {i+1} de la matriz de costos"
            
            #  costo máximo
            try:
                costo_max = float(lineas[5 + m].strip())
                if costo_max < 0:
                    return False, "El costo máximo no puede ser negativo"
            except ValueError:
                return False, "Error en el formato del costo máximo"
            
            # movimientos máximos
            try:
                mov_max = int(lineas[5 + m + 1].strip())
                if mov_max < 0:
                    return False, "Los movimientos máximos no pueden ser negativos"
            except ValueError:
                return False, "Error en el formato de movimientos máximos"
            
            return True, f"Archivo válido: {n} personas, {m} opiniones"
            
        except Exception as e:
            return False, f"Error inesperado durante la validación: {str(e)}"
    
    def parsear_resultados_minizinc(self, salida):
        """Parsea la salida de MiniZinc para extraer información relevante"""
        resultado_parseado = []
        
        try:
            lineas = salida.split('\n')
            
            # Buscar información del solver y estadísticas
            for linea in lineas:
                linea = linea.strip()
                
                # Información del solver
                if "% solver:" in linea.lower() or "solver:" in linea.lower():
                    resultado_parseado.append(f"Solver utilizado: {linea}")
                
                # Tiempo de ejecución
                if "time elapsed:" in linea.lower() or "solving time:" in linea.lower():
                    resultado_parseado.append(f" {linea}")
                
                # Estado de la solución
                if linea in ["=====OPTIMAL=====", "=====SATISFIABLE=====", "=====UNSATISFIABLE=====", 
                           "=====UNKNOWN=====", "=====UNBOUNDED=====", "=====ERROR====="]:
                    estado_map = {
                        "=====OPTIMAL=====": "SOLUCIÓN ÓPTIMA ENCONTRADA",
                        "=====SATISFIABLE=====": "SOLUCIÓN FACTIBLE ENCONTRADA",
                        "=====UNSATISFIABLE=====": "NO HAY SOLUCIÓN FACTIBLE",
                        "=====UNKNOWN=====": "ESTADO DESCONOCIDO",
                        "=====UNBOUNDED=====": "PROBLEMA NO ACOTADO",
                        "=====ERROR=====": " ERROR EN LA EJECUCIÓN"
                    }
                    resultado_parseado.append(f"\n{estado_map.get(linea, linea)}\n")
                
                # Variables de decisión
                if "=" in linea and not linea.startswith("%") and not linea.startswith("====="):
                    if any(keyword in linea.lower() for keyword in ['extremismo', 'costo', 'movimientos', 'x_']):
                        resultado_parseado.append(f" {linea}")
                
                # Función objetivo
                if linea.startswith("Extremismo final:") or "objetivo:" in linea.lower():
                    resultado_parseado.append(f" {linea}")
            
            # Buscar matriz de movimientos si existe
            matriz_movimientos = []
            capturando_matriz = False
            
            for linea in lineas:
                if "movimientos:" in linea.lower() or "matriz" in linea.lower():
                    capturando_matriz = True
                    continue
                
                if capturando_matriz and linea.strip():
                    if linea.startswith("[") or "|" in linea:
                        matriz_movimientos.append(linea.strip())
                    else:
                        capturando_matriz = False
            
            if matriz_movimientos:
                resultado_parseado.append("\n📋 MATRIZ DE MOVIMIENTOS:")
                for fila in matriz_movimientos:
                    resultado_parseado.append(f"   {fila}")
            
            # Si no hay contenido parseado, mostrar mensaje
            if not resultado_parseado:
                resultado_parseado.append(" No se pudo extraer información estructurada de los resultados.")
                resultado_parseado.append("Revisa la pestaña 'Salida Completa' para ver todos los detalles.")
            
            return "\n".join(resultado_parseado)
            
        except Exception as e:
            return f" Error al parsear resultados: {str(e)}\n\nRevisa la pestaña 'Salida Completa' para ver la salida original."
    
    def manejar_errores_minizinc(self, stderr, returncode):
        """Maneja errores específicos de MiniZinc y proporciona mensajes útiles"""
        mensajes_error = []
        
        # Errores comunes de MiniZinc
        errores_conocidos = {
            "syntax error": " Error de sintaxis en el modelo MiniZinc",
            "type error": "Error de tipos en el modelo",
            "assertion failed": " Fallo en una aserción del modelo",
            "unsatisfiable": " El problema no tiene solución factible",
            "timeout": "Tiempo límite excedido",
            "memory": " Error de memoria insuficiente",
            "file not found": " Archivo no encontrado",
            "permission denied": "Permisos insuficientes para acceder al archivo"
        }
        
        error_encontrado = False
        for patron, mensaje in errores_conocidos.items():
            if patron in stderr.lower():
                mensajes_error.append(mensaje)
                error_encontrado = True
                break
        
        if not error_encontrado:
            if returncode != 0:
                mensajes_error.append(f" Error de ejecución (código: {returncode})")
        
        # Sugerencias basadas en el tipo de error
        if "syntax error" in stderr.lower():
            mensajes_error.append(" Sugerencia: Revisa la sintaxis del archivo .mzn")
        elif "type error" in stderr.lower():
            mensajes_error.append(" Sugerencia: Verifica los tipos de datos en el modelo")
        elif "unsatisfiable" in stderr.lower():
            mensajes_error.append(" Sugerencia: Reduce las restricciones o aumenta los límites")
        elif "timeout" in stderr.lower():
            mensajes_error.append(" Sugerencia: Aumenta el tiempo límite o usa un solver más rápido")
        elif "file not found" in stderr.lower():
            mensajes_error.append("Sugerencia: Verifica que los archivos existan y las rutas sean correctas")
        
        return "\n".join(mensajes_error) if mensajes_error else None
    
    def iniciar_monitor_cola(self):
        """Monitorea la cola de mensajes y actualiza la interfaz"""
        try:
            while True:
                mensaje_tipo, contenido = self.mensaje_queue.get_nowait()
                
                if mensaje_tipo == "texto":
                    self.texto_resultados.insert(tk.END, contenido)
                    self.texto_resultados.see(tk.END)
                elif mensaje_tipo == "texto_procesado":
                    self.texto_procesado.delete(1.0, tk.END)
                    self.texto_procesado.insert(1.0, contenido)
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
            # Validar archivo al seleccionarlo
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                es_valido, mensaje = self.validar_formato_entrada(contenido)
                if es_valido:
                    self.archivo_entrada = archivo
                    self.entrada_path.set(archivo)
                    self.status_label.config(text=f" {mensaje}")
                else:
                    respuesta = messagebox.askyesno(
                        "Archivo con errores", 
                        f"Se encontraron errores en el archivo:\n\n{mensaje}\n\n¿Deseas seleccionarlo de todas formas?"
                    )
                    if respuesta:
                        self.archivo_entrada = archivo
                        self.entrada_path.set(archivo)
                        self.status_label.config(text=" Archivo seleccionado con advertencias")
                    else:
                        self.status_label.config(text=" Archivo no seleccionado")
            except Exception as e:
                messagebox.showerror("Error", f"Error al leer el archivo:\n{str(e)}")
    
    def validar_entrada_manual(self):
        """Valida manualmente el archivo de entrada seleccionado"""
        if not self.archivo_entrada or not os.path.exists(self.archivo_entrada):
            messagebox.showwarning("Advertencia", "Por favor selecciona primero un archivo de entrada válido.")
            return
        
        try:
            with open(self.archivo_entrada, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            es_valido, mensaje = self.validar_formato_entrada(contenido)
            
            if es_valido:
                messagebox.showinfo("Validación exitosa", f"{mensaje}")
            else:
                messagebox.showerror("Errores encontrados", f"{mensaje}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al validar el archivo:\n{str(e)}")
    
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
            self.mensaje_queue.put(("status", "Validando archivos..."))
            
            # Leer y validar archivo de entrada
            with open(self.archivo_entrada, 'r', encoding='utf-8') as f:
                contenido_entrada = f.read()
            
            es_valido, mensaje_validacion = self.validar_formato_entrada(contenido_entrada)
            if not es_valido:
                self.mensaje_queue.put(("error", f"El archivo de entrada no es válido:\n\n{mensaje_validacion}"))
                return

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
            self.mensaje_queue.put(("texto", f"Validación: {mensaje_validacion}\n"))

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
                '--statistics',
                '--verbose-solving' 
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
                bufsize=1,
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
                        if any(keyword in line.lower() for keyword in ['extremismo', 'costo', 'movimientos', 'resultado', 'optimal', 'satisfiable']):
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
                
                # Parsear y mostrar resultados procesados
                resultados_parseados = self.parsear_resultados_minizinc(stdout)
                self.mensaje_queue.put(("texto_procesado", resultados_parseados))
                
                if stderr:
                    self.mensaje_queue.put(("texto", "\n=== INFORMACIÓN DEL SOLVER ===\n"))
                    self.mensaje_queue.put(("texto", stderr))
                self.mensaje_queue.put(("status", f"Completado en {elapsed_time:.2f}s"))
            else:
                # Manejar errores específicos de MiniZinc
                error_msg = stderr if stderr else stdout
                mensaje_error = self.manejar_errores_minizinc(error_msg, self.proceso_activo.returncode)
                
                self.mensaje_queue.put(("texto", f"\n=== ERROR ({elapsed_time:.2f}s) ===\n"))
                if mensaje_error:
                    self.mensaje_queue.put(("texto", mensaje_error + "\n\n"))
                self.mensaje_queue.put(("texto", f"Salida original del error:\n{error_msg}"))
                self.mensaje_queue.put(("texto_procesado", f"EJECUCIÓN FALLIDA\n\n{mensaje_error or 'Error desconocido'}\n\nRevisa la pestaña 'Salida Completa' para más detalles."))
                self.mensaje_queue.put(("status", f" Error en la ejecución ({elapsed_time:.2f}s)"))

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
                self.mensaje_queue.put(("texto_procesado", " EJECUCIÓN CANCELADA POR EL USUARIO"))
                self.mensaje_queue.put(("status", " Cancelado por el usuario"))
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
        
        # Validar archivos antes de ejecutar
        if not self.archivo_entrada or not os.path.exists(self.archivo_entrada):
            messagebox.showerror("Error", "Por favor selecciona un archivo de entrada válido.")
            return
            
        if not self.archivo_modelo or not os.path.exists(self.archivo_modelo):
            messagebox.showerror("Error", "Por favor selecciona un archivo de modelo válido.")
            return
        
        # Deshabilitar botón y mostrar progreso
        self.btn_ejecutar.config(state='disabled')
        self.btn_cancelar.config(state='normal')
        self.progress.start()
        self.status_label.config(text=" Iniciando...")
        
        # Limpiar resultados previos
        self.texto_resultados.delete(1.0, tk.END)
        self.texto_procesado.delete(1.0, tk.END)
        
        # Ejecutar en hilo separado
        self.hilo_activo = threading.Thread(target=self.ejecutar_modelo_thread)
        self.hilo_activo.daemon = True
        self.hilo_activo.start()
    
    def limpiar_resultados(self):
        self.texto_resultados.delete(1.0, tk.END)
        self.texto_procesado.delete(1.0, tk.END)
        self.status_label.config(text="Listo para ejecutar")
    
    def guardar_resultados(self):
        # Preguntar qué tipo de resultados guardar
        respuesta = messagebox.askyesnocancel(
            "Tipo de resultados", 
            "¿Qué tipo de resultados deseas guardar?\n\n"
            "Sí: Resultados procesados (más legibles)\n"
            "No: Salida completa (formato original)\n"
            "Cancelar: No guardar nada"
        )
        
        if respuesta is None:  # Cancelar
            return
        
        if respuesta:  # Sí - Resultados procesados
            contenido = self.texto_procesado.get(1.0, tk.END)
            tipo = "procesados"
        else:  # No - Salida completa
            contenido = self.texto_resultados.get(1.0, tk.END)
            tipo = "completos"
        
        if contenido.strip():
            archivo = filedialog.asksaveasfilename(
                title=f"Guardar resultados {tipo}",
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
            )
            if archivo:
                try:
                    with open(archivo, 'w', encoding='utf-8') as f:
                        f.write(f"=== RESULTADOS MINEXT ({tipo.upper()}) ===\n")
                        f.write(f"Generado: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Archivo entrada: {os.path.basename(self.archivo_entrada) if self.archivo_entrada else 'N/A'}\n")
                        f.write(f"Archivo modelo: {os.path.basename(self.archivo_modelo) if self.archivo_modelo else 'N/A'}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(contenido)
                    messagebox.showinfo("Éxito", f"Resultados {tipo} guardados correctamente.")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al guardar: {str(e)}")
        else:
            messagebox.showwarning("Advertencia", "No hay resultados para guardar.")
    
    def convertir_archivos(self):
        """Función para convertir archivos TXT a DZN con validación mejorada"""
        archivos = filedialog.askopenfilenames(
            title="Selecciona los archivos .txt/.mext",
            filetypes=[("Archivos soportados", "*.txt;*.mext"), ("Archivos de texto", "*.txt"), ("Archivos MinExt", "*.mext")]
        )

        if not archivos:
            return

        carpeta_salida = filedialog.askdirectory(title="Selecciona la carpeta de destino")
        if not carpeta_salida:
            return

        convertidos = 0
        errores = []
        
        for ruta in archivos:
            try:
                with open(ruta, "r", encoding='utf-8') as archivo:
                    contenido = archivo.read()
                
                # Validar antes de convertir
                es_valido, mensaje = self.validar_formato_entrada(contenido)
                if not es_valido:
                    errores.append(f"{os.path.basename(ruta)}: {mensaje}")
                    continue
                
                contenido_dzn = self.convertir_contenido_txt_a_dzn(contenido)

                nombre_base = os.path.splitext(os.path.basename(ruta))[0]
                ruta_salida = os.path.join(carpeta_salida, nombre_base + ".dzn")

                with open(ruta_salida, "w", encoding='utf-8') as salida:
                    salida.write(f"% Archivo DZN generado automáticamente\n")
                    salida.write(f"% Origen: {os.path.basename(ruta)}\n")
                    salida.write(f"% Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    salida.write(contenido_dzn)
                
                convertidos += 1

            except Exception as e:
                errores.append(f"{os.path.basename(ruta)}: {str(e)}")

        # Mostrar resultados de la conversión
        mensaje_resultado = f"{convertidos} archivos convertidos correctamente."
        
        if errores:
            mensaje_resultado += f"\n\nErrores en {len(errores)} archivos:\n"
            for error in errores[:5]:  # Mostrar máximo 5 errores
                mensaje_resultado += f"• {error}\n"
            if len(errores) > 5:
                mensaje_resultado += f"... y {len(errores) - 5} errores más."
        
        if convertidos > 0:
            messagebox.showinfo("Conversión completada", mensaje_resultado)
        else:
            messagebox.showerror("Error en conversión", mensaje_resultado)

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
    
    # Configurar estilos personalizados
    style.configure("Accent.TButton", font=("Arial", 10, "bold"))
    
    app = MinExtGUI(root)
    
    # Mostrar mensaje de bienvenida
    root.after(1000, lambda: app.status_label.config(text="Selecciona los archivos de entrada y modelo para comenzar"))
    
    root.mainloop()

if __name__ == "__main__":
    main()