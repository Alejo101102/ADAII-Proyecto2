import tkinter as tk
from tkinter import filedialog, messagebox
import os

def convertir_contenido_txt_a_dzn_con_nombres_claros(contenido_txt):
    lineas = contenido_txt.strip().split("\n")
    num_personas = lineas[0]
    num_opiniones = lineas[1]
    distribucion_inicial = lineas[2]
    valores_extremismo = lineas[3]
    costos_extra = lineas[4]
    matriz_costos_lineas = lineas[5:5 + int(num_opiniones)]
    costo_maximo = lineas[5 + int(num_opiniones)]
    movimientos_maximos = lineas[6 + int(num_opiniones)]

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

def convertir_archivos():
    archivos = filedialog.askopenfilenames(
        title="Selecciona los archivos .txt",
        filetypes=[("Archivos de texto", "*.txt")]
    )

    if not archivos:
        return

    carpeta_salida = filedialog.askdirectory(title="Selecciona la carpeta de destino")
    if not carpeta_salida:
        return

    for ruta in archivos:
        try:
            with open(ruta, "r") as archivo:
                contenido = archivo.read()
            contenido_dzn = convertir_contenido_txt_a_dzn_con_nombres_claros(contenido)

            nombre_base = os.path.splitext(os.path.basename(ruta))[0]
            ruta_salida = os.path.join(carpeta_salida, nombre_base + ".dzn")

            with open(ruta_salida, "w") as salida:
                salida.write(contenido_dzn)

        except Exception as e:
            messagebox.showerror("Error", f"Error con el archivo {ruta}:\n{str(e)}")
            return

    messagebox.showinfo("Conversión exitosa", f"{len(archivos)} archivos convertidos con nombres claros.")

# GUI
ventana = tk.Tk()
ventana.title("Convertidor TXT → DZN (variables claras)")
ventana.geometry("360x140")
ventana.resizable(False, False)

boton = tk.Button(ventana, text="Seleccionar archivos y convertir", command=convertir_archivos)
boton.pack(expand=True, pady=35)

ventana.mainloop()
