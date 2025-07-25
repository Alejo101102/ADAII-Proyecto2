import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import subprocess
import tempfile
import threading

class MinExtGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto MinExt - Minimizar Extremismo en Poblaciones")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Variables para almacenar rutas de archivos
        self.archivo_entrada = None
        self.archivo_modelo = None
        
        self.crear_interfaz()
    
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
        
        # Botón principal de ejecución
        ejecutar_frame = ttk.Frame(main_frame)
        ejecutar_frame.grid(row=2, column=0, columnspan=3, pady=(10, 20))
        
        self.btn_ejecutar = ttk.Button(ejecutar_frame, text="Ejecutar Modelo MinExt", 
                                      command=self.ejecutar_modelo, style="Accent.TButton")
        self.btn_ejecutar.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(ejecutar_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(5, 0))
        
        # Área de resultados
        resultados_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        resultados_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        resultados_frame.columnconfigure(0, weight=1)
        resultados_frame.rowconfigure(0, weight=1)
        
        self.texto_resultados = scrolledtext.ScrolledText(resultados_frame, 
                                                         wrap=tk.WORD, 
                                                         height=20, 
                                                         font=("Consolas", 10))
        self.texto_resultados.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame para botones adicionales
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(botones_frame, text="Limpiar Resultados", 
                  command=self.limpiar_resultados).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(botones_frame, text="Guardar Resultados", 
                  command=self.guardar_resultados).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(botones_frame, text="Convertir TXT → DZN", 
                  command=self.convertir_archivos).pack(side=tk.LEFT)
        
        # Configurar weights para redimensionamiento
        main_frame.rowconfigure(3, weight=1)
    
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
        """Ejecuta el modelo en un hilo separado"""
        temp_dzn_path = None
        try:
            # depuración
            self.root.after(0, lambda: self.mostrar_mensaje(f"[DEBUG] self.archivo_entrada: {self.archivo_entrada}\n"))
            self.root.after(0, lambda: self.mostrar_mensaje(f"[DEBUG] self.archivo_modelo: {self.archivo_modelo}\n"))

            # Validar archivos
            if not self.archivo_entrada or not os.path.exists(self.archivo_entrada):
                self.root.after(0, lambda: messagebox.showerror("Error", f"Por favor selecciona un archivo de entrada válido.\n[DEBUG] Valor: {self.archivo_entrada}"))
                return

            if not self.archivo_modelo or not os.path.exists(self.archivo_modelo):
                self.root.after(0, lambda: messagebox.showerror("Error", f"Por favor selecciona un archivo de modelo válido.\n[DEBUG] Valor: {self.archivo_modelo}"))
                return

            # Leer archivo de entrada
            with open(self.archivo_entrada, 'r', encoding='utf-8') as f:
                contenido_entrada = f.read()

            # Convertir a formato DZN
            contenido_dzn = self.convertir_contenido_txt_a_dzn(contenido_entrada)

            # Crear archivo temporal DZN
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dzn', delete=False, encoding='utf-8') as temp_dzn:
                temp_dzn.write(contenido_dzn)
                temp_dzn_path = temp_dzn.name

            # Mostrar progreso
            self.root.after(0, lambda: self.mostrar_mensaje("Ejecutando modelo MiniZinc...\n"))
            self.root.after(0, lambda: self.mostrar_mensaje(f"Archivo de entrada: {self.archivo_entrada}\n"))
            self.root.after(0, lambda: self.mostrar_mensaje(f"Archivo de modelo: {self.archivo_modelo}\n\n"))

            # Ejecutar MiniZinc
            cmd = ['minizinc', '--solver', 'Gecode', self.archivo_modelo, temp_dzn_path]

            self.root.after(0, lambda: self.mostrar_mensaje("Ejecutando comando: " + " ".join(cmd) + "\n\n"))

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            stdout, stderr = process.communicate()

            # Mostrar resultados
            if process.returncode == 0:
                self.root.after(0, lambda: self.mostrar_mensaje("=== RESULTADOS ===\n"))
                self.root.after(0, lambda: self.mostrar_mensaje(stdout))
                if stderr:
                    self.root.after(0, lambda: self.mostrar_mensaje("\n=== ADVERTENCIAS ===\n"))
                    self.root.after(0, lambda: self.mostrar_mensaje(stderr))
            else:
                error_msg = stderr if stderr else stdout
                self.root.after(0, lambda msg=error_msg: self.mostrar_mensaje("Error al ejecutar el modelo:\n"))
                self.root.after(0, lambda msg=error_msg: self.mostrar_mensaje(msg))

        except Exception as e:
            error_str = str(e)
            self.root.after(0, lambda msg=error_str: messagebox.showerror("Error", f"Error durante la ejecución: {msg}"))

        finally:
            # Limpiar archivo temporal
            if temp_dzn_path and os.path.exists(temp_dzn_path):
                try:
                    os.unlink(temp_dzn_path)
                except:
                    pass

            # Detener progress bar y habilitar botón
            self.root.after(0, self.finalizar_ejecucion)
    
    def finalizar_ejecucion(self):
        """Finaliza la ejecución y restaura el estado de la interfaz"""
        self.progress.stop()
        self.btn_ejecutar.config(state='normal')
    
    def ejecutar_modelo(self):
        # Deshabilitar botón y mostrar progreso
        self.btn_ejecutar.config(state='disabled')
        self.progress.start()
        
        # Ejecutar en hilo separado
        thread = threading.Thread(target=self.ejecutar_modelo_thread)
        thread.daemon = True
        thread.start()
    
    def mostrar_mensaje(self, mensaje):
        """Agrega un mensaje al área de resultados"""
        self.texto_resultados.insert(tk.END, mensaje)
        self.texto_resultados.see(tk.END)
    
    def limpiar_resultados(self):
        self.texto_resultados.delete(1.0, tk.END)
    
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