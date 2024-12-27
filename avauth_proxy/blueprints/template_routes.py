from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from avauth_proxy.models import Template, Base
from avauth_proxy.utils.decorator_utils import log_route_error
import os

template_bp = Blueprint('templates', __name__)

# Create database session
engine = create_engine('sqlite:///database.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()

@template_bp.route('/templates', methods=['GET'])
@log_route_error()
def list_templates():
    """Display the template management interface."""
    templates = db_session.query(Template).all()
    return render_template('templates/templates.html', templates=templates)

@template_bp.route('/templates/add', methods=['POST'])
@log_route_error()
def add_template():
    """Add a new Nginx template."""
    data = request.json
    name = data.get('name')
    content = data.get('content')

    if not name or not content:
        return jsonify({'error': 'Name and content are required'}), 400

    # Check if template already exists
    existing = db_session.query(Template).filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Template name already exists'}), 400

    new_template = Template(name=name, content=content)
    db_session.add(new_template)

    try:
        db_session.commit()
        return jsonify({'message': 'Template added successfully'}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@template_bp.route('/templates/<int:template_id>', methods=['PUT'])
@log_route_error()
def update_template(template_id):
    """Update an existing template."""
    template = db_session.query(Template).get(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404

    data = request.json
    template.name = data.get('name', template.name)
    template.content = data.get('content', template.content)

    try:
        db_session.commit()
        return jsonify({'message': 'Template updated successfully'})
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@template_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@log_route_error()
def delete_template(template_id):
    """Delete a template."""
    template = db_session.query(Template).get(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404

    try:
        db_session.delete(template)
        db_session.commit()
        return jsonify({'message': 'Template deleted successfully'})
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@template_bp.route('/templates/preview', methods=['POST'])
@log_route_error()
def preview_template():
    """Preview template with given parameters."""
    data = request.json
    template_id = data.get('template_id')
    parameters = data.get('parameters', {})

    template = db_session.query(Template).get(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404

    try:
        from jinja2 import Template as J2Template
        rendered = J2Template(template.content).render(**parameters)
        return jsonify({'preview': rendered})
    except Exception as e:
        return jsonify({'error': f'Error rendering template: {str(e)}'}), 400
