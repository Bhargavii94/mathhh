# explore.py
from flask import Blueprint, render_template, request, jsonify # <-- Make sure jsonify is imported
from flask_login import login_required
from models import Video
from extensions import db
# --- ADD THESE NEW IMPORTS ---
import base64
import io
import numpy as np
import matplotlib
matplotlib.use('Agg') # This is important for running Matplotlib in a non-GUI environment
import matplotlib.pyplot as plt
# -----------------------------

explore = Blueprint('explore', __name__)

@explore.route('/explore')
@login_required
def explore_videos():
    # --- YOUR EXISTING explore_videos FUNCTION REMAINS UNCHANGED ---
    topics = db.session.query(Video.topic).distinct().all()
    class_levels = db.session.query(Video.class_level).distinct().all()
    topics = sorted([t[0] for t in topics])
    class_levels = sorted([c[0] for c in class_levels])
    selected_topic = request.args.get('topic')
    selected_class_level = request.args.get('class_level')
    query = Video.query
    if selected_topic and selected_topic != 'All Topics':
        query = query.filter_by(topic=selected_topic)
    if selected_class_level and selected_class_level != 'All Classes':
        query = query.filter_by(class_level=selected_class_level)
    videos = query.order_by(Video.uploaded_at.desc()).all()
    return render_template('explore.html',
                           videos=videos,
                           topics=topics,
                           class_levels=class_levels,
                           selected_topic=selected_topic,
                           selected_class_level=selected_class_level)

# --- ADD THIS ENTIRE NEW ROUTE AT THE END OF THE FILE ---
@explore.route('/graph-plotter', methods=['GET', 'POST'])
@login_required
def graph_plotter():
    if request.method == 'POST':
        data = request.get_json()
        expression = data.get('expression', '')

        # Sanitize the expression to make it safe
        allowed_names = {
            'x': None, 'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
            'sqrt': np.sqrt, 'exp': np.exp, 'log': np.log, 'log10': np.log10,
            'pi': np.pi, 'e': np.e
        }
        
        try:
            # Prepare the x-axis values
            x = np.linspace(-10, 10, 400)
            allowed_names['x'] = x

            # Safely evaluate the expression
            y = eval(expression, {"__builtins__": {}}, allowed_names)

            # Generate the plot
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot(x, y, color='#1abc9c', linewidth=2)
            ax.set_title(f'Graph of y = {expression}', fontsize=16, family='sans-serif')
            ax.set_xlabel('x-axis', fontsize=12)
            ax.set_ylabel('y-axis', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.axhline(0, color='black', linewidth=0.5)
            ax.axvline(0, color='black', linewidth=0.5)
            fig.tight_layout()
            
            # Save plot to a memory buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            plt.close(fig)
            buf.seek(0)

            # Encode the image to base64 and send it back
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return jsonify({'image': image_base64})

        except Exception as e:
            return jsonify({'error': f'Invalid expression. Check syntax or allowed functions.'}), 400

    return render_template('graph_plotter.html')
# --------------------------------------------------------
# (Keep all your existing imports and code)
# ...

# --- ADD THIS NEW ROUTE AT THE END OF THE FILE ---
@explore.route('/matrix-calculator', methods=['GET', 'POST'])
@login_required
def matrix_calculator():
    if request.method == 'POST':
        try:
            data = request.get_json()
            matrix_a = np.array(data['matrix_a'], dtype=float)
            matrix_b = np.array(data['matrix_b'], dtype=float)
            operation = data['operation']

            if operation == 'add':
                if matrix_a.shape != matrix_b.shape:
                    return jsonify({'error': 'Matrices must have the same dimensions for addition.'}), 400
                result = matrix_a + matrix_b
            elif operation == 'subtract':
                if matrix_a.shape != matrix_b.shape:
                    return jsonify({'error': 'Matrices must have the same dimensions for subtraction.'}), 400
                result = matrix_a - matrix_b
            elif operation == 'multiply':
                if matrix_a.shape[1] != matrix_b.shape[0]:
                    return jsonify({'error': 'The number of columns in Matrix A must equal the number of rows in Matrix B for multiplication.'}), 400
                result = np.dot(matrix_a, matrix_b)
            else:
                return jsonify({'error': 'Invalid operation.'}), 400
            
            return jsonify({'result': result.tolist()})

        except Exception as e:
            return jsonify({'error': 'Invalid matrix format or calculation error.'}), 400
            
    return render_template('matrix_calculator.html')
# (Keep all your existing imports and code)
# --- ADD THIS NEW IMPORT FOR THE SOLVER ---
import cmath # Use cmath to handle complex roots gracefully
# -----------------------------------------

# (Your existing routes for explore_videos, graph_plotter, matrix_calculator are here)
# ...

# --- ADD THIS ENTIRE NEW ROUTE AT THE END OF THE FILE ---
@explore.route('/quadratic-solver', methods=['GET', 'POST'])
@login_required
def quadratic_solver():
    if request.method == 'POST':
        try:
            data = request.get_json()
            a = float(data['a'])
            b = float(data['b'])
            c = float(data['c'])

            if a == 0:
                return jsonify({'error': 'The coefficient "a" cannot be zero for a quadratic equation.'}), 400

            # Calculate the discriminant
            discriminant = (b**2) - (4*a*c)

            # Find two solutions
            sol1 = (-b - cmath.sqrt(discriminant)) / (2 * a)
            sol2 = (-b + cmath.sqrt(discriminant)) / (2 * a)
            
            # Format the solutions to be readable strings
            # This handles complex numbers like '3+2j' automatically
            result = {
                'sol1': str(sol1).replace('j', 'i'),
                'sol2': str(sol2).replace('j', 'i')
            }
            return jsonify(result)

        except Exception as e:
            return jsonify({'error': 'Invalid input. Please enter valid numbers for a, b, and c.'}), 400
            
    return render_template('quadratic_solver.html')