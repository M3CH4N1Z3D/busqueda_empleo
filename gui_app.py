import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import tempfile
import logging
from pdf2docx import Converter
from main_flow import ejecutar_flujo_principal

# Configurar logging
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Búsqueda de Empleo Automatizada")
        self.geometry("500x350")

        self.pdf_path = None

        # Título
        self.title_label = ctk.CTkLabel(self, text="Automatización de Búsqueda de Empleo", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=20)

        # Correo
        self.email_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.email_frame.pack(pady=10, padx=20, fill="x")
        
        self.email_label = ctk.CTkLabel(self.email_frame, text="Correo Electrónico:")
        self.email_label.pack(side="left", padx=10)
        
        self.email_entry = ctk.CTkEntry(self.email_frame, placeholder_text="ejemplo@correo.com", width=250)
        self.email_entry.pack(side="right", padx=10, expand=True, fill="x")

        # Selección de PDF
        self.pdf_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pdf_frame.pack(pady=10, padx=20, fill="x")
        
        self.pdf_button = ctk.CTkButton(self.pdf_frame, text="Seleccionar CV (PDF)", command=self.seleccionar_pdf)
        self.pdf_button.pack(side="left", padx=10)
        
        self.pdf_label = ctk.CTkLabel(self.pdf_frame, text="Ningún archivo seleccionado", text_color="gray")
        self.pdf_label.pack(side="left", padx=10, expand=True, fill="x")

        # Botón Iniciar
        self.start_button = ctk.CTkButton(self, text="Iniciar Búsqueda", command=self.iniciar_proceso, font=ctk.CTkFont(size=15, weight="bold"), height=40)
        self.start_button.pack(pady=30)

        # Estado
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=5)

    def seleccionar_pdf(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar Currículum",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if filepath:
            self.pdf_path = filepath
            filename = os.path.basename(filepath)
            self.pdf_label.configure(text=filename, text_color="black")

    def mostrar_mensaje(self, tipo, titulo, mensaje):
        if tipo == "info":
            messagebox.showinfo(titulo, mensaje)
        elif tipo == "error":
            messagebox.showerror(titulo, mensaje)
        elif tipo == "warning":
            messagebox.showwarning(titulo, mensaje)

    def actualizar_estado(self, mensaje):
        self.status_label.configure(text=mensaje)

    def iniciar_proceso(self):
        email = self.email_entry.get().strip()
        if not email:
            messagebox.showwarning("Advertencia", "Por favor, ingrese un correo electrónico.")
            return
        
        if not self.pdf_path:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un archivo PDF.")
            return

        self.start_button.configure(state="disabled")
        self.status_label.configure(text="Procesando...")
        print("\n" + "="*50)
        print("INICIANDO PROCESO DE BÚSQUEDA DE EMPLEO")
        print("="*50)
        print(f"Correo destino: {email}")
        print(f"Archivo CV: {self.pdf_path}")

        # Ejecutar en un hilo separado para no bloquear la GUI
        threading.Thread(target=self.ejecutar_tarea, args=(email, self.pdf_path), daemon=True).start()

    def ejecutar_tarea(self, email, pdf_path):
        temp_docx_path = None
        try:
            print("\n[Paso 1] Preparando archivos...")
            print("Convirtiendo PDF a DOCX...")
            self.after(0, lambda: self.actualizar_estado("Convirtiendo PDF a DOCX..."))
            
            # Crear archivo temporal para el DOCX
            fd, temp_docx_path = tempfile.mkstemp(suffix=".docx")
            os.close(fd) # Cerrar el file descriptor inmediatamente
            
            # Convertir PDF a DOCX
            cv = Converter(pdf_path)
            try:
                cv.convert(temp_docx_path, start=0, end=None)
            finally:
                cv.close()
            print("Conversión de PDF a DOCX completada.")

            print("\n[Paso 2] Iniciando flujo principal (Análisis, Búsqueda y Evaluación)...")
            self.after(0, lambda: self.actualizar_estado("Buscando ofertas y evaluando..."))
            
            # Ejecutar el flujo principal
            ejecutar_flujo_principal(temp_docx_path, email)
            
            print("\n[Paso 3] Finalización")
            print("Proceso completado con éxito. Revise su correo electrónico.")
            self.after(0, lambda: self.actualizar_estado("Proceso completado con éxito."))
            self.after(0, lambda: self.mostrar_mensaje("info", "Éxito", "El proceso ha finalizado correctamente. Revise su correo."))
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n[ERROR] Ocurrió un error durante el proceso: {error_msg}")
            logging.exception("Error en el proceso principal")
            self.after(0, lambda: self.actualizar_estado("Error en el proceso."))
            self.after(0, lambda: self.mostrar_mensaje("error", "Error", f"Ocurrió un error:\n{error_msg}"))
        finally:
            # Limpiar archivo temporal
            if temp_docx_path and os.path.exists(temp_docx_path):
                try:
                    os.remove(temp_docx_path)
                except Exception as e:
                    print(f"No se pudo eliminar el archivo temporal {temp_docx_path}: {e}")
            
            self.after(0, lambda: self.start_button.configure(state="normal"))

if __name__ == "__main__":
    app = App()
    app.mainloop()
