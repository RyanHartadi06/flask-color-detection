from flask import Blueprint, Response
from app.controllers import item_controller
from app.services.color_service import generate_video_stream
from app.controllers.color_controller import ColorController

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return item_controller.index()

@main.route('/create', methods=['GET', 'POST'])
def create():
    return item_controller.create()

@main.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit(item_id):
    return item_controller.edit(item_id)

@main.route('/delete/<int:item_id>')
def delete(item_id):
    return item_controller.delete(item_id)

@main.route('/video_feed')
def video_feed():
    return Response(ColorController.generate_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@main.route('/detect-color')
def detect_color():
    return ColorController.detect_color()