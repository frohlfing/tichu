import os
import shutil
import pydoc
import sys

def generate_doc(module_name):
    """
    Generiert die HTML-Dokumentation für das angegebene Modul und verschiebt sie in das Ausgabeverzeichnis.

    Args:
        module_name (str): Der Name des Moduls, für das die Dokumentation generiert werden soll.
    """

    output_dir = "./docs/pydoc"

    # Generiere die HTML-Dokumentation
    pydoc.writedoc(module_name)

    # Erstelle das Ausgabeverzeichnis, falls es nicht existiert
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Verschiebe die generierte HTML-Datei in das Ausgabeverzeichnis
    html_file = f'{module_name}.html'
    shutil.move(html_file, os.path.join(output_dir, html_file))

    print(f'Dokumentation für {module_name} wurde in {output_dir} gespeichert.')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Verwendung: python generate_doc.py <modulname>")
    else:
        generate_doc(sys.argv[1])

