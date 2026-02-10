import joblib
import json
import numpy as np
import os

selected_features = ["odor", "spore-print-color", "gill-color", "ring-type", "stalk-surface-above-ring"] 

def init():
    """
    This function runs once when the container starts.
    It loads the SVM model into memory.
    """
    global model
    
    model_path = os.path.join(
        os.getenv("AZUREML_MODEL_DIR"), 
        "best_svm_model.pkl"
    )
    
    model = joblib.load(model_path)
    print("SVM model loaded successfully")

def run(raw_data):
    """
    This function runs every time someone calls your API.
    It receives JSON data, makes predictions, and returns results.
    """
    try:
        data = json.loads(raw_data)['data']
        
        data = np.array(data)
        
        if data.shape[1] != len(selected_features):
            return {
                "error": f"Expected {len(selected_features)} features, got {data.shape[1]}"
            }
        
        predictions = model.predict(data)
        
        return {"predictions": predictions.tolist()}
    
    except Exception as e:
        return {"error": str(e)}
