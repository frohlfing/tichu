# Was bedeutet ```if __name__ == "__main__":```?

Das ist ein gängiges Konstrukt in Python, das verwendet wird, um sicherzustellen, dass ein bestimmter Codeblock nur 
ausgeführt wird, wenn das Skript direkt ausgeführt wird, und nicht, wenn es als Modul importiert wird. 

```__name__```: Dies ist eine spezielle Variable in Python, die den Namen des aktuellen Moduls enthält. 

- Direkte Ausführung: Wenn das Skript direkt ausgeführt wird (z.B. durch ```python script.py```),  
ist ```__name__``` gleich "__main__", und der Codeblock innerhalb der if-Bedingung wird ausgeführt.

- Import als Modul: Wenn das Skript als Modul in einem anderen Skript importiert wird (z.B. ```import script```), 
ist ```__name__``` gleich dem Namen des Moduls ("script"), und der Codeblock innerhalb der if-Bedingung wird nicht ausgeführt.