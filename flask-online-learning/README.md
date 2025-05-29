# Flask Online Learning

This project implements a Flask application that provides an interface for online learning using various machine learning models. The application allows users to create models, fit them with data, and make predictions through a simple API.

## Project Structure

```
flask-online-learning
├── app
│   ├── __init__.py
│   ├── routes.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── sklearn_model.py
│   │   └── river_model.py
├── requirements.txt
├── run.py
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd flask-online-learning
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python run.py
   ```

2. The API will be available at `http://127.0.0.1:5000`.

## API Endpoints

- **Create Model**
  - **Endpoint:** `/create_model`
  - **Method:** `POST`
  - **Body:** `{ "model_name": "string" }`
  - **Description:** Creates a new model with the specified name.

- **Fit Model**
  - **Endpoint:** `/fit`
  - **Method:** `POST`
  - **Body:** `{ "model_name": "string", "x": [array], "y": "label" }`
  - **Description:** Fits the specified model with the provided data.

- **Predict**
  - **Endpoint:** `/predict`
  - **Method:** `POST`
  - **Body:** `{ "model_name": "string", "x": [array] }`
  - **Description:** Makes a prediction using the specified model.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.