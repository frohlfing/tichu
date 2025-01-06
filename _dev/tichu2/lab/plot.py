import matplotlib.pyplot as plt
import numpy as np

# Beispieldaten
x = np.linspace(0, 6*np.pi, 100)
y_sin = np.sin(x)
y_cos = np.cos(x)

# Plotter initialisieren
plt.ion()  # Interactive-Modus aktivieren (this is the call that allows dynamic plotting)
fig = plt.figure(figsize=(18, 6))  # Breite x Höhe; das Diagramm wird jetzt angezeigt

# Verlustfunktion
ax_loss = fig.add_subplot(1, 2, 1)  # rows, cols, index
plt.title('Trainingsverlauf')
plt.xlabel('Epochen')
plt.ylabel('Wert der Verlustfunktion')
plt.legend(loc='upper right')
plt.grid(True)
line_loss, = ax_loss.plot(x, y_sin, color='black', linestyle=':', marker='', label='Training')
line_val_loss, = ax_loss.plot(x, y_cos, color='blue', linestyle='-', marker='', label='Validierung')
# plt.draw()

# Trefferquote
ax_acc = fig.add_subplot(1, 2, 2)  # rows, cols, index
plt.title('Trainingsverlauf')
plt.xlabel('Epochen')
plt.ylabel('Trefferquote')
plt.legend(loc='upper right')
plt.grid(True)
line_acc, = ax_acc.plot(x, y_sin, color='black', linestyle=':', marker='', label='Training')
line_val_acc, = ax_acc.plot(x, y_cos, color='blue', linestyle='-', marker='', label='Validierung')

# Life update
for phase in np.linspace(0, 10*np.pi, 500):
    y_sin = np.sin(x + phase)
    y_cos = np.cos(x + phase)
    line_loss.set_ydata(y_sin)  # alternativ: line_loss.set_data(x, y_sin)
    line_val_loss.set_ydata(y_cos)
    plt.pause(0.001)  # necessary to allow the plotter to catch up

plt.ioff()  # Interactive-Modus deaktivieren
plt.show()  # ansonsten schließt sich das Plot-Fenster
