import os
import eventlet
eventlet.monkey_patch()  # Esto es necesario para que SocketIO funcione con eventlet

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, send
import pymysql

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

# Rutas para la aplicación
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('inicio'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usu']
        password = request.form['passwd']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM login WHERE BINARY usu = %s AND passwd = %s", (usuario, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = usuario
            return redirect(url_for('inicio'))
        else:
            return "Usuario o contraseña incorrectos"
    return render_template('login.html')

#NUEVO
@app.route('/inicio')
def inicio():
    return render_template('inicio.html')




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario = request.form['usu']
        password = request.form['passwd']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO login (usu, passwd) VALUES (%s, %s)", (usuario, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Error al registrar el usuario: Ya existe este usuario (las mayúsculas y minúsculas las obvias)"

    return render_template('register.html')


@app.route('/message')
def message():
    if 'user' in session:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, mensaje FROM mensajes ORDER BY id ASC")
            messages = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Error al obtener los mensajes: {e}")
            messages = []

        return render_template('message.html', user=session['user'], messages=messages)
    return redirect(url_for('login'))



@socketio.on("message")
def handle_message(message):
    # Aquí `message` es el objeto recibido del cliente, así que accede directamente a sus claves
    user = message.get('user')  # Asegúrate de que el mensaje contiene el campo 'user'
    message_content = message.get('message')  # Y también el campo 'message'

    print(f"Message from {user}: {message_content}")

    # Guardar el mensaje en la base de datos
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s)", (user, message_content))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al guardar el mensaje en la base de datos: {e}")

    # Emitir el mensaje a todos los clientes conectados
    send({"user": user, "message": message_content}, broadcast=True)



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


#######################################

@app.route('/tareas')
def listar_tareas():
    """Muestra las tareas pendientes y completadas con su información."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE estado = 'pendiente'")
    tareas_pendientes = cursor.fetchall()

    cursor.execute("SELECT * FROM tareas WHERE estado = 'completada'")
    tareas_completadas = cursor.fetchall()
    
    conn.close()
    
    return render_template('tareas.html', pendientes=tareas_pendientes, completadas=tareas_completadas)


@app.route('/tareas/agregar', methods=['POST'])
def agregar_tarea():
    """Agrega una nueva tarea con el usuario en sesión."""
    if 'user' not in session:
        return redirect(url_for('login'))

    tarea = request.form['tarea']
    descripcion = request.form['descripcion']
    fecha = request.form['fecha']
    fecha_caducidad = request.form['fecha_caducidad']
    usuario = session['user']  # Usuario en sesión

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tareas (tarea, descripcion, fecha, fecha_caducidad, usuario) VALUES (%s, %s, %s, %s, %s)",
        (tarea, descripcion, fecha, fecha_caducidad, usuario)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('listar_tareas'))


@app.route('/tareas/completar/<int:tarea_id>')
def completar_tarea(tarea_id):
    """Marca una tarea como completada."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tareas SET estado = 'completada' WHERE id = %s", (tarea_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('listar_tareas'))

@app.route('/tareas/eliminar/<int:tarea_id>')
def eliminar_tarea(tarea_id):
    """Elimina una tarea."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tareas WHERE id = %s", (tarea_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('listar_tareas'))






if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
