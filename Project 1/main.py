from flask import Flask, request, jsonify
import json
import csv
import os

app = Flask(__name__)
DATA_CSV = 'students.csv'
DATA_JSON = 'students.json'

# Load dữ liệu từ file JSON nếu tồn tại
if os.path.exists(DATA_JSON):
    with open(DATA_JSON, 'r', encoding='utf-8') as file:
        students = json.load(file)
else:
    students = [
        {"id": 1, "name": "Nguyen Van A", "age": 16, "grade": "10A1"},
        {"id": 2, "name": "Tran Thi B", "age": 17, "grade": "11A2"},
        {"id": 3, "name": "Le Van C", "age": 15, "grade": "9B"},
        {"id": 4, "name": "Pham Thi D", "age": 16, "grade": "10C1"},
        {"id": 5, "name": "Hoang Van E", "age": 18, "grade": "12A3"},
    ]

# Hàm tự tăng ID
def get_next_id():
    return max(student["id"] for student in students) + 1 if students else 1

# Ghi vào CSV
def save_students_to_csv():
    with open(DATA_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "age", "grade"])
        writer.writeheader()
        writer.writerows(students)

# Ghi vào JSON
def save_students_to_json():
    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(students, f, indent=4, ensure_ascii=False)

# Ghi cả 2
def save_all():
    save_students_to_csv()
    save_students_to_json()

# Lấy danh sách học sinh
@app.route('/students', methods=['GET'])
def get_students():
    return jsonify(students)

# Lấy học sinh theo ID
@app.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = next((s for s in students if s["id"] == student_id), None)
    return jsonify(student) if student else ("Not Found", 404)

# Thêm học sinh mới
@app.route('/students', methods=['POST'])
def add_student():
    data = request.get_json()
    new_student = {
        "id": get_next_id(),
        "name": data.get("name"),
        "age": data.get("age"),
        "grade": data.get("grade"),
    }
    students.append(new_student)
    save_all()
    return jsonify(new_student), 201

# Cập nhật học sinh
@app.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    student = next((s for s in students if s["id"] == student_id), None)
    if not student:
        return ("Not Found", 404)
    data = request.get_json()
    student.update({
        "name": data.get("name", student["name"]),
        "age": data.get("age", student["age"]),
        "grade": data.get("grade", student["grade"]),
    })
    save_all()
    return jsonify(student)

# Xoá học sinh
@app.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = next((s for s in students if s["id"] == student_id), None)
    if not student:
        return ("Not Found", 404)
    students.remove(student)
    save_all()
    return jsonify({"message": "Student deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=8080)