from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io, base64, cirq
from qiskit import QuantumCircuit
import matplotlib.pyplot as plt

app = FastAPI()

# IMPORTANT: Allows your GitHub Pages frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuantumRequest(BaseModel):
    code: str
    framework: str

def get_qiskit_circuit(code, framework):
    if framework == "OpenQASM 2.0":
        return QuantumCircuit.from_qasm_str(code)
    
    elif framework == "Qiskit (Python)":
        ldict = {}
        exec(code, globals(), ldict)
        # Finds the first QuantumCircuit object in the executed code
        for v in ldict.values():
            if isinstance(v, QuantumCircuit): return v
        raise ValueError("No QuantumCircuit object 'qc' found.")

    elif framework == "Cirq":
        ldict = {}
        exec(f"import cirq\n{code}", globals(), ldict)
        # Finds the first Cirq Circuit object
        for v in ldict.values():
            if isinstance(v, cirq.Circuit):
                return QuantumCircuit.from_qasm_str(cirq.qasm(v))
        raise ValueError("No Cirq 'circuit' found.")
    
    else:
        raise ValueError(f"Framework {framework} conversion not yet implemented.")

@app.post("/visualize")
async def visualize(req: QuantumRequest):
    try:
        qc = get_qiskit_circuit(req.code, req.framework)
        buf = io.BytesIO()
        qc.draw('mpl', style='iqp').savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return {"image": f"data:image/png;base64,{img_base64}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
