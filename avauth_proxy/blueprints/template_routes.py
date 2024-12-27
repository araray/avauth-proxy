from flask import Blueprint, request, jsonify, render_template
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from avauth_proxy.models import Template, Base

engine = create_engine('sqlite:///database.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

template_bp = Blueprint('templates', __name__)

@template_bp.route('/templates', methods=['GET'])
def list_templates():
    templates = session.query(Template).all()
    return render_template('templates.html', templates=templates)

@template_bp.route('/templates', methods=['POST'])
def create_template():
    data = request.json
    new_template = Template(name=data['name'], content=data['content'])
    session.add(new_template)
    session.commit()
    return jsonify({"message": "Template added successfully"}), 201

@template_bp.route('/templates/<int:id>', methods=['PUT'])
def update_template(id):
    template = session.query(Template).get(id)
    if not template:
        return jsonify({"message": "Template not found"}), 404
    data = request.json
    template.name = data.get('name', template.name)
    template.content = data.get('content', template.content)
    session.commit()
    return jsonify({"message": "Template updated successfully"}), 200

@template_bp.route('/templates/<int:id>', methods=['DELETE'])
def delete_template(id):
    template = session.query(Template).get(id)
    if not template:
        return jsonify({"message": "Template not found"}), 404
    session.delete(template)
    session.commit()
    return jsonify({"message": "Template deleted successfully"}), 200
