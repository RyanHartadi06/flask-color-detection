items = []

def get_all_items():
    return items

def add_item(name):
    item = {'id': len(items) + 1, 'name': name}
    items.append(item)

def get_item_by_id(item_id):
    return next((item for item in items if item['id'] == item_id), None)

def update_item(item_id, new_name):
    item = get_item_by_id(item_id)
    if item:
        item['name'] = new_name

def delete_item(item_id):
    global items
    items = [item for item in items if item['id'] != item_id]
